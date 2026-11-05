import os

# Must happen BEFORE the app is imported: load_dotenv() never overrides variables
# that are already set, so the real database, Gemini key and secrets in .env are never used.
os.environ["DATABASE_URL"] = "sqlite://"  # in-memory SQLite, separate from the real database
os.environ["GEMINI_API_KEY"] = "fake-test-key"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ADMIN_EMAILS"] = "admin@example.com"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

import database

# One shared in-memory connection, usable from the test client's thread.
test_engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
database.engine = test_engine
database.SessionLocal.configure(bind=test_engine)

import ai_utils  # noqa: E402
import email_utils  # noqa: E402
import main  # noqa: E402
from auth import create_access_token  # noqa: E402

# Safety net: stop at once if the app is not on the test database.
assert main.engine.dialect.name == "sqlite", "Tests must never run on the real database"
assert database.SessionLocal.kw["bind"] is test_engine


@pytest.fixture(autouse=True)
def fresh_database():
    database.Base.metadata.drop_all(bind=test_engine)
    database.Base.metadata.create_all(bind=test_engine)
    main._ai_calls_by_ip.clear()
    yield


@pytest.fixture(autouse=True)
def no_real_services(monkeypatch):
    """Block the real Gemini API and the real SMTP server in every test."""
    from google import genai

    def refuse_real_gemini(*args, **kwargs):
        raise AssertionError("A test tried to create a real Gemini client")

    monkeypatch.setattr(genai, "Client", refuse_real_gemini)
    monkeypatch.setattr(ai_utils, "_new_client", refuse_real_gemini)
    monkeypatch.setattr(ai_utils, "AI_RETRY_DELAY_SECONDS", 0)

    sent_emails = []
    monkeypatch.setattr(email_utils, "_send", sent_emails.append)
    return sent_emails


@pytest.fixture
def sent_emails(no_real_services):
    return no_real_services


@pytest.fixture
def client():
    return TestClient(main.app)


@pytest.fixture
def db():
    session = database.SessionLocal()
    yield session
    session.close()


@pytest.fixture
def admin_headers():
    return {"Authorization": "Bearer " + create_access_token({"sub": "admin@example.com"})}


@pytest.fixture
def other_user_headers():
    return {"Authorization": "Bearer " + create_access_token({"sub": "someone@example.com"})}
