"""SIPRE foundation API with transactional data, sessions and health checks."""

import logging
import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, SQLAlchemyError

from app import __version__
from app.api import router as api_router
from app.db.health import create_database_engine, database_ready
from app.security import event
from app.security import router as auth_router
from app.settings import Settings

logger = logging.getLogger("sipre.http")


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        engine = create_database_engine(config)
        application.state.engine = engine
        try:
            yield
        finally:
            if engine is not None:
                engine.dispose()

    application = FastAPI(
        title="SIPRE — Backend SIMULATED",
        version=__version__,
        description="Prototipo académico SIMULATED. SIPRE recomienda; la autoridad humana decide.",
        lifespan=lifespan,
    )
    application.state.settings = config
    application.include_router(auth_router)
    application.include_router(api_router)

    @application.exception_handler(RequestValidationError)
    async def invalid_request(request, exc):
        # Pydantic errors can include submitted passwords/raw data: expose locations only.
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "fields": [{"loc": list(e["loc"]), "type": e["type"]} for e in exc.errors()],
                    "correlation_id": getattr(request.state, "correlation_id", None),
                }
            },
        )

    @application.exception_handler(HTTPException)
    async def rejected(request, exc):
        # One envelope for every client error: code is a stable machine-readable token.
        code = exc.detail if isinstance(exc.detail, str) else "REQUEST_REJECTED"
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": code,
                    "correlation_id": getattr(request.state, "correlation_id", None),
                }
            },
            headers=exc.headers,
        )

    @application.exception_handler(DBAPIError)
    async def database_error(request, exc):
        sqlstate = getattr(exc.orig, "sqlstate", "") or ""
        logger.error(
            "database_error correlation_id=%s sqlstate=%s message=%s",
            getattr(request.state, "correlation_id", None),
            sqlstate,
            str(exc.orig).splitlines()[0] if str(exc.orig) else "",
        )
        status = (
            409
            if sqlstate in ("23505", "40001", "40P01")
            else (422 if sqlstate.startswith(("22", "23")) else 503)
        )
        return JSONResponse(
            status_code=status,
            content={
                "error": {
                    "code": "DATA_CONFLICT"
                    if status == 409
                    else ("DATA_INTEGRITY_ERROR" if status == 422 else "DATABASE_UNAVAILABLE"),
                    "correlation_id": getattr(request.state, "correlation_id", None),
                }
            },
        )

    @application.middleware("http")
    async def correlation(request: Request, call_next):
        # Generate server-side: untrusted request headers cannot inject log content.
        correlation_id = str(uuid4())
        request.state.correlation_id = correlation_id
        started = time.monotonic()
        response = await call_next(request)
        if response.status_code == 403 and getattr(request.state, "actor_id", None):
            # Persist denied access independently of the rolled-back business transaction.
            try:
                with request.app.state.engine.begin() as db:
                    event(db, request.state.actor_id, "ACCESS_DENIED", "http", correlation_id)
            except SQLAlchemyError:
                logger.warning("denial_audit_unavailable correlation_id=%s", correlation_id)
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        logger.info(
            "request_completed correlation_id=%s method=%s status=%d duration_ms=%.2f",
            correlation_id,
            request.method,
            response.status_code,
            (time.monotonic() - started) * 1000,
        )
        return response

    @application.get("/api/v1/health/live", tags=["infrastructure"])
    def live():
        return {"status": "alive", "mode": config.mode, "version": __version__}

    @application.get("/api/v1/health/ready", tags=["infrastructure"])
    def ready(request: Request):
        if not database_ready(request.app.state.engine):
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "mode": config.mode,
                    "error": {
                        "code": "DATABASE_UNAVAILABLE",
                        "correlation_id": request.state.correlation_id,
                    },
                },
            )
        return {"status": "ready", "mode": config.mode}

    return application


app = create_app()
