"""Server-side sessions and explicit capabilities. No role inheritance."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import text

from app import schemas

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=1)
DUMMY_HASH = hasher.hash(secrets.token_urlsafe(32))
CAPABILITIES = {
    "ADMIN": {"users", "catalog", "audit"},
    "OPERATOR": {"read", "write", "catalog", "create_emergency"},
    "ANALYST": {"read", "snapshot", "jobs"},
    "DECISION_MAKER": {"read", "approve_estimate"},
    "VIEWER": {"read"},
}


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def database(request: Request):
    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        raise HTTPException(503, "DATABASE_UNAVAILABLE")
    with engine.begin() as connection:
        yield connection


def event(db, actor, action, object_type, object_id, emergency_id=None):
    db.execute(
        text("""INSERT INTO audit.events(actor_id,action,object_type,object_id,emergency_id)
        VALUES(:actor,:action,:type,:id,:emergency)"""),
        {
            "actor": actor,
            "action": action,
            "type": object_type,
            "id": str(object_id),
            "emergency": emergency_id,
        },
    )


def principal(request: Request, db=Depends(database, scope="function")):
    token = request.cookies.get("sipre_session", "")
    row = (
        db.execute(
            text("""SELECT s.*,u.active FROM core.sessions s JOIN core.users u USING(user_id)
        WHERE token_hash=:hash AND expires_at>now() AND u.active"""),
            {"hash": digest(token)},
        )
        .mappings()
        .first()
    )
    if row is None:
        raise HTTPException(401, "AUTHENTICATION_REQUIRED")
    request.state.actor_id = row["user_id"]
    roles = set(
        db.execute(
            text("SELECT role_code FROM core.user_roles WHERE user_id=:id"), {"id": row["user_id"]}
        ).scalars()
    )
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        csrf = request.headers.get("x-csrf-token", "")
        if not secrets.compare_digest(row["csrf_hash"], digest(csrf)):
            raise HTTPException(403, "CSRF_REQUIRED")
    db.execute(
        text("SELECT set_config('sipre.actor_id',:actor,true)"), {"actor": str(row["user_id"])}
    )
    return {
        "user_id": row["user_id"],
        "roles": roles,
        "capabilities": set().union(*(CAPABILITIES[r] for r in roles)),
    }


def require(user, capability):
    if capability not in user["capabilities"]:
        raise HTTPException(403, "CAPABILITY_REQUIRED")


def scoped(db, user, emergency_id, capability="read", mutable=False):
    require(user, capability)
    if not db.execute(
        text("""SELECT 1 FROM core.emergency_members
        WHERE emergency_id=:e AND user_id=:u"""),
        {"e": emergency_id, "u": user["user_id"]},
    ).scalar():
        raise HTTPException(403, "EMERGENCY_ACCESS_DENIED")
    suffix = " FOR UPDATE" if mutable else ""
    row = (
        db.execute(
            text("SELECT * FROM ops.emergencies WHERE emergency_id=:id" + suffix),
            {"id": emergency_id},
        )
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(404, "EMERGENCY_NOT_FOUND")
    if mutable and row["state"] in ("CLOSED", "CANCELLED"):
        raise HTTPException(409, "EMERGENCY_CLOSED")
    return row


@router.post("/login")
def login(
    body: schemas.Login,
    request: Request,
    response: Response,
    db=Depends(database, scope="function"),
):
    # A DB row makes throttling effective across workers. No password/login in audit.
    key = digest(body.login.casefold())
    db.execute(
        text("""INSERT INTO core.login_attempts(login_key) VALUES(:k)
        ON CONFLICT DO NOTHING"""),
        {"k": key},
    )
    attempt = (
        db.execute(
            text("SELECT * FROM core.login_attempts WHERE login_key=:k FOR UPDATE"), {"k": key}
        )
        .mappings()
        .one()
    )
    now = datetime.now(UTC)
    failures = attempt["failures"] if now - attempt["window_start"] < timedelta(minutes=15) else 0
    if failures >= 10:
        db.commit()
        raise HTTPException(429, "LOGIN_RATE_LIMIT")
    user = (
        db.execute(
            text("SELECT * FROM core.users WHERE login=:login"), {"login": body.login.casefold()}
        )
        .mappings()
        .first()
    )
    valid = False
    try:
        valid = hasher.verify(
            user["password_hash"] if user else DUMMY_HASH, body.password.get_secret_value()
        )
    except (VerificationError, InvalidHashError):
        pass
    if not valid or not user or not user["active"]:
        db.execute(
            text("""UPDATE core.login_attempts SET failures=:n,
            window_start=CASE WHEN :n=1 THEN now() ELSE window_start END WHERE login_key=:k"""),
            {"k": key, "n": failures + 1},
        )
        event(db, None, "LOGIN_FAILED", "auth", key)
        db.commit()  # Persist rate limit even though the HTTP response is an error.
        raise HTTPException(401, "INVALID_CREDENTIALS")
    db.execute(text("DELETE FROM core.login_attempts WHERE login_key=:k"), {"k": key})
    # Opportunistic hygiene: drop this user's expired sessions through the user_id index.
    db.execute(
        text("DELETE FROM core.sessions WHERE user_id=:u AND expires_at < now()"),
        {"u": user["user_id"]},
    )
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    hours = request.app.state.settings.session_hours
    db.execute(
        text("""INSERT INTO core.sessions(token_hash,user_id,csrf_hash,expires_at)
        VALUES(:t,:u,:c,:expires)"""),
        {
            "t": digest(token),
            "u": user["user_id"],
            "c": digest(csrf),
            "expires": now + timedelta(hours=hours),
        },
    )
    event(db, user["user_id"], "LOGIN", "auth", user["user_id"])
    response.set_cookie(
        "sipre_session",
        token,
        httponly=True,
        samesite="strict",
        secure=request.app.state.settings.cookie_secure,
        max_age=hours * 3600,
        path="/",
    )
    return {"user_id": str(user["user_id"]), "csrf_token": csrf}


@router.get("/me")
def me(user=Depends(principal)):
    return {
        "user_id": str(user["user_id"]),
        "roles": sorted(user["roles"]),
        "capabilities": sorted(user["capabilities"]),
    }


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    db.execute(
        text("DELETE FROM core.sessions WHERE token_hash=:t"),
        {"t": digest(request.cookies.get("sipre_session", ""))},
    )
    event(db, user["user_id"], "LOGOUT", "auth", user["user_id"])
    response.delete_cookie("sipre_session", path="/")
