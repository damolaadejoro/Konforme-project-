import os

import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

# Fake credentials so nothing can reach a real AWS account
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_DEFAULT_REGION", "eu-west-1")

import store  # noqa: E402
from main import app  # noqa: E402
from rate_limit import limiter  # noqa: E402


@pytest.fixture()
def dynamodb():
    """A fresh in-memory DynamoDB table (moto) for each test."""
    with mock_aws():
        store.reset_connections()
        store.create_table()
        yield
        store.reset_connections()


@pytest.fixture()
def db_session(dynamodb):
    return store.Session()


@pytest.fixture()
def client(dynamodb):
    """FastAPI test client backed by the mocked table, with rate limiting disabled."""
    limiter.enabled = False
    with TestClient(app) as c:
        yield c
    limiter.enabled = True


@pytest.fixture()
def registered_user(client):
    """Register a user and return the auth data."""
    res = client.post("/api/v1/auth/register", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "SecurePass123!",
    })
    assert res.status_code == 200
    return res.json()


@pytest.fixture()
def auth_header(registered_user):
    """Authorization header for a registered user."""
    return {"Authorization": f"Bearer {registered_user['access_token']}"}
