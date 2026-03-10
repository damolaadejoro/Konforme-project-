"""Tests for user registration, login, and JWT-protected endpoints."""


# ── Registration ──────────────────────────────────────────────────────────────


class TestRegister:
    def test_register_success(self, client):
        res = client.post("/api/v1/auth/register", json={
            "name": "Alice",
            "email": "alice@example.com",
            "password": "Password123!",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["access_token"]
        assert data["token_type"] == "bearer"
        assert data["account_name"] == "Alice"
        assert data["email"] == "alice@example.com"
        assert data["account_id"]

    def test_register_duplicate_email(self, client):
        payload = {
            "name": "Alice",
            "email": "alice@example.com",
            "password": "Password123!",
        }
        client.post("/api/v1/auth/register", json=payload)
        res = client.post("/api/v1/auth/register", json=payload)
        assert res.status_code == 409
        assert "already exists" in res.json()["detail"]

    def test_register_short_password(self, client):
        res = client.post("/api/v1/auth/register", json={
            "name": "Alice",
            "email": "alice@example.com",
            "password": "short",
        })
        assert res.status_code == 422
        assert "8 characters" in res.json()["detail"]

    def test_register_invalid_email(self, client):
        res = client.post("/api/v1/auth/register", json={
            "name": "Alice",
            "email": "not-an-email",
            "password": "Password123!",
        })
        assert res.status_code == 422  # pydantic validation

    def test_register_missing_fields(self, client):
        res = client.post("/api/v1/auth/register", json={
            "email": "alice@example.com",
        })
        assert res.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────────


class TestLogin:
    def test_login_success(self, client, registered_user):
        res = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "SecurePass123!",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["access_token"]
        assert data["token_type"] == "bearer"
        assert data["account_id"] == registered_user["account_id"]
        assert data["email"] == "test@example.com"

    def test_login_wrong_password(self, client, registered_user):
        res = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword",
        })
        assert res.status_code == 401
        assert "Invalid email or password" in res.json()["detail"]

    def test_login_nonexistent_email(self, client):
        res = client.post("/api/v1/auth/login", json={
            "email": "nobody@example.com",
            "password": "Password123!",
        })
        assert res.status_code == 401
        assert "Invalid email or password" in res.json()["detail"]

    def test_login_invalid_email_format(self, client):
        res = client.post("/api/v1/auth/login", json={
            "email": "bad-email",
            "password": "Password123!",
        })
        assert res.status_code == 422


# ── JWT Protection ────────────────────────────────────────────────────────────


class TestJWTProtection:
    def test_protected_endpoint_with_valid_token(self, client, auth_header):
        res = client.get("/api/v1/accounts", headers=auth_header)
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "Test User"
        assert data["is_active"] is True

    def test_protected_endpoint_without_token(self, client):
        res = client.get("/api/v1/accounts")
        assert res.status_code == 401

    def test_protected_endpoint_with_invalid_token(self, client):
        res = client.get("/api/v1/accounts", headers={
            "Authorization": "Bearer totally-invalid-token",
        })
        assert res.status_code == 401
        assert "Invalid or expired token" in res.json()["detail"]

    def test_protected_endpoint_with_malformed_header(self, client):
        res = client.get("/api/v1/accounts", headers={
            "Authorization": "NotBearer sometoken",
        })
        assert res.status_code == 401

    def test_token_from_register_works(self, client):
        reg = client.post("/api/v1/auth/register", json={
            "name": "Bob",
            "email": "bob@example.com",
            "password": "Password123!",
        })
        token = reg.json()["access_token"]
        res = client.get("/api/v1/accounts", headers={
            "Authorization": f"Bearer {token}",
        })
        assert res.status_code == 200
        assert res.json()["name"] == "Bob"

    def test_token_from_login_works(self, client, registered_user):
        login_res = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "SecurePass123!",
        })
        token = login_res.json()["access_token"]
        res = client.get("/api/v1/accounts", headers={
            "Authorization": f"Bearer {token}",
        })
        assert res.status_code == 200
        assert res.json()["name"] == "Test User"


# ── Account isolation ─────────────────────────────────────────────────────────


class TestAccountIsolation:
    def test_cannot_access_other_account_score(self, client):
        # Register two users
        r1 = client.post("/api/v1/auth/register", json={
            "name": "User1", "email": "u1@example.com", "password": "Password123!",
        })
        r2 = client.post("/api/v1/auth/register", json={
            "name": "User2", "email": "u2@example.com", "password": "Password123!",
        })
        token1 = r1.json()["access_token"]
        account1_id = r1.json()["account_id"]
        account2_id = r2.json()["account_id"]

        # Verify the two accounts are different
        assert account1_id != account2_id

        # User1 tries to access User2's score — should be denied
        res = client.get(
            f"/api/v1/score/{account2_id}",
            headers={"Authorization": f"Bearer {token1}"},
        )
        assert res.status_code == 403


# ── Health check (public) ────────────────────────────────────────────────────


class TestHealthCheck:
    def test_health_is_public(self, client):
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"
