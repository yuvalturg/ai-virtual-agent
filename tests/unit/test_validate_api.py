"""
Unit tests for Authentication Validation API endpoints.

Tests OAuth session-based authentication validation.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models import RoleEnum, User


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.add = MagicMock()
    return mock_session


@pytest.fixture
def sample_user():
    """Create sample user."""
    return User(
        id=uuid.uuid4(),
        username="test-user",
        email="test@example.com",
        role=RoleEnum.user,
    )


class TestValidateEndpoint:
    """Test main validate endpoint with OAuth sessions."""

    @patch("backend.app.api.v1.validate.get_user_from_session")
    def test_validate_authenticated_user(
        self, mock_get_user, test_client, mock_db_session, sample_user
    ):
        """Test validation with authenticated user session."""
        from backend.app.api.v1.validate import get_db

        mock_get_user.return_value = sample_user

        auth_request = {
            "api_key": "test-key",
            "request": {
                "path": "/",
                "headers": {},
                "params": {},
            },
        }

        app.dependency_overrides[get_db] = lambda: mock_db_session
        response = test_client.post("/api/v1/validate/", json=auth_request)
        app.dependency_overrides.clear()

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["principal"] == "test-user"
        assert data["message"] == "Authentication successful"
        assert data["attributes"]["roles"] == ["user"]

    @patch("backend.app.api.v1.validate.get_user_from_session")
    def test_validate_admin_user(
        self, mock_get_user, test_client, mock_db_session
    ):
        """Test validation with admin user session."""
        from backend.app.api.v1.validate import get_db

        admin_user = User(
            id=uuid.uuid4(),
            username="admin",
            email="admin@example.com",
            role=RoleEnum.admin,
        )
        mock_get_user.return_value = admin_user

        auth_request = {
            "api_key": "test-key",
            "request": {
                "path": "/",
                "headers": {},
                "params": {},
            },
        }

        app.dependency_overrides[get_db] = lambda: mock_db_session
        response = test_client.post("/api/v1/validate/", json=auth_request)
        app.dependency_overrides.clear()

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["principal"] == "admin"
        assert data["attributes"]["roles"] == ["admin"]

    @patch("backend.app.api.v1.validate.get_user_from_session")
    def test_validate_no_session(
        self, mock_get_user, test_client, mock_db_session
    ):
        """Test validation when user has no session."""
        from backend.app.api.v1.validate import get_db

        mock_get_user.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

        auth_request = {
            "api_key": "test-key",
            "request": {
                "path": "/",
                "headers": {},
                "params": {},
            },
        }

        app.dependency_overrides[get_db] = lambda: mock_db_session
        response = test_client.post("/api/v1/validate/", json=auth_request)
        app.dependency_overrides.clear()

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestValidateWithHeaders:
    """Test validate_with_headers endpoint."""

    @patch("backend.app.api.v1.validate.get_sa_token")
    @patch("backend.app.api.v1.validate.make_http_request")
    def test_validate_with_headers_success(self, mock_http, mock_token, test_client):
        """Test successful validation with headers."""
        mock_token.return_value = "test-token"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "principal": "test-user",
            "attributes": {"roles": ["user"]},
            "message": "Success",
        }
        mock_http.return_value = mock_response

        response = test_client.post(
            "/api/v1/validate/test",
            headers={
                "X-Forwarded-User": "test-user",
                "X-Forwarded-Email": "test@example.com",
            },
        )

        assert response.status_code == status.HTTP_200_OK

    @patch("backend.app.api.v1.validate.get_sa_token")
    @patch("backend.app.api.v1.validate.make_http_request")
    def test_validate_with_headers_auth_failed(
        self, mock_http, mock_token, test_client
    ):
        """Test validation with headers when auth fails."""
        mock_token.return_value = "test-token"
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_http.return_value = mock_response

        response = test_client.post(
            "/api/v1/validate/test",
            headers={
                "X-Forwarded-User": "test-user",
                "X-Forwarded-Email": "test@example.com",
            },
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch("backend.app.api.v1.validate.get_sa_token")
    @patch("backend.app.api.v1.validate.make_http_request")
    def test_validate_with_headers_invalid_response(
        self, mock_http, mock_token, test_client
    ):
        """Test validation with invalid response format."""
        mock_token.return_value = "test-token"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalid": "data"}
        mock_http.return_value = mock_response

        response = test_client.post(
            "/api/v1/validate/test",
            headers={
                "X-Forwarded-User": "test-user",
                "X-Forwarded-Email": "test@example.com",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestMakeHttpRequest:
    """Test make_http_request helper function."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_make_http_request_get(self, mock_client_class):
        """Test GET request."""
        from backend.app.api.v1.validate import make_http_request

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client

        response = await make_http_request(
            "http://test.com", {"Authorization": "Bearer token"}
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_make_http_request_post(self, mock_client_class):
        """Test POST request."""
        from backend.app.api.v1.validate import make_http_request

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client

        response = await make_http_request(
            "http://test.com", {}, method="POST", json_data={"key": "value"}
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_make_http_request_timeout(self, mock_client_class):
        """Test request timeout handling."""
        import httpx
        from fastapi import HTTPException

        from backend.app.api.v1.validate import make_http_request

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        mock_client_class.return_value.__aenter__.return_value = mock_client

        with pytest.raises(HTTPException) as exc_info:
            await make_http_request("http://test.com", {})

        assert exc_info.value.status_code == 408

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_make_http_request_error(self, mock_client_class):
        """Test request error handling."""
        from fastapi import HTTPException

        from backend.app.api.v1.validate import make_http_request

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Connection error"))
        mock_client_class.return_value.__aenter__.return_value = mock_client

        with pytest.raises(HTTPException) as exc_info:
            await make_http_request("http://test.com", {})

        assert exc_info.value.status_code == 503
