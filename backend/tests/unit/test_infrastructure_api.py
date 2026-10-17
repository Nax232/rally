import logging
from uuid import UUID

import pytest
from app.db.health import database_ready
from app.main import create_app
from app.settings import Settings
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError
from sqlalchemy.exc import OperationalError


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("SIPRE_DATABASE_URL", raising=False)
    monkeypatch.delenv("SIPRE_MODE", raising=False)
    with TestClient(create_app(Settings())) as session:
        yield session


def test_liveness_does_not_claim_database_ready(client):
    assert client.get("/api/v1/health/live").json()["status"] == "alive"
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DATABASE_UNAVAILABLE"
    assert response.json()["mode"] == "SIMULATED"


def test_readiness_requires_postgis_query(monkeypatch, client):
    calls = []

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def execute(self, statement):
            calls.append(str(statement))
            return self

        def scalar(self):
            return True

    class Engine:
        def connect(self):
            return Connection()

    monkeypatch.setattr(client.app.state, "engine", Engine())
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert "PostGIS_Version()" in calls[0]


def test_connection_error_does_not_leak_credentials(monkeypatch, client, caplog):
    class Unavailable:
        def connect(self):
            raise OperationalError(
                "postgresql://private:secret-value@host/db", {}, Exception("secret-value")
            )

    monkeypatch.setattr(client.app.state, "engine", Unavailable())
    with caplog.at_level(logging.INFO, logger="sipre.http"):
        response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert "secret-value" not in response.text + caplog.text
    assert "private" not in response.text


def test_correlation_ids_are_server_generated_and_not_cached(client):
    first = client.get("/api/v1/health/live", headers={"X-Correlation-ID": "untrusted"})
    second = client.get("/api/v1/health/live")
    assert UUID(first.headers["x-correlation-id"]).version == 4
    assert first.headers["x-correlation-id"] != second.headers["x-correlation-id"]
    assert first.headers["cache-control"] == "no-store"


def test_no_automatic_domain_or_decision_operations(client):
    # Data endpoints now exist but cannot operate without their database/authentication.
    assert client.post("/api/v1/emergencies", json={}).status_code == 503
    assert client.post("/api/v1/recommendations/example/accept", json={}).status_code == 404


def test_every_client_error_uses_one_envelope(client):
    unavailable = client.post("/api/v1/emergencies", json={})
    assert unavailable.status_code == 503
    assert set(unavailable.json()["error"]) == {"code", "correlation_id"}
    assert unavailable.json()["error"]["code"] == "DATABASE_UNAVAILABLE"
    # Session lookup needs the database; unavailability outranks authentication.
    unauthenticated = client.get("/api/v1/auth/me")
    assert unauthenticated.status_code == 503
    assert unauthenticated.json()["error"]["code"] == "DATABASE_UNAVAILABLE"
    # The database dependency short-circuits before body validation is reachable.
    assert client.post("/api/v1/auth/login", json={"login": "x"}).status_code == 503


def test_unconfigured_dependency_is_not_ready():
    assert database_ready(None) is False


@pytest.mark.parametrize("mode", ["LIVE", "PRODUCTION", "REAL"])
def test_real_operation_modes_are_rejected(mode):
    with pytest.raises(ValidationError):
        Settings(mode=mode)


@pytest.mark.parametrize("url", ["sqlite:///db", "postgresql://a:b@host/db", "not-a-url"])
def test_other_database_drivers_are_rejected(url):
    with pytest.raises(ValidationError):
        Settings(database_url=SecretStr(url))


def test_invalid_settings_error_hides_secret_value():
    with pytest.raises(ValidationError) as error:
        Settings(database_url="invalid-secret-connection")
    assert "invalid-secret-connection" not in str(error.value)


def test_valid_database_url_is_not_printed_in_settings():
    settings = Settings(database_url=SecretStr("postgresql+psycopg://u:private@host/db"))
    assert "private" not in repr(settings)
