import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from rate_limit import limiter


@pytest.fixture()
def db_session():
    """Create an in-memory SQLite database for each test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    """FastAPI test client with overridden DB dependency and rate limiting disabled."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    limiter.enabled = False
    with TestClient(app) as c:
        yield c
    limiter.enabled = True
    app.dependency_overrides.clear()


@pytest.fixture()
def registered_user(client):
    """Register a user and return the auth data."""
    res = client.post("/api/v1/auth/register", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "securepass123",
    })
    assert res.status_code == 200
    return res.json()


@pytest.fixture()
def auth_header(registered_user):
    """Authorization header for a registered user."""
    return {"Authorization": f"Bearer {registered_user['access_token']}"}
