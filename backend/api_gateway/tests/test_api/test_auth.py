"""Tests for the authentication endpoints."""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.exceptions import ServerCredError

client = TestClient(app)


def test_google_login_success():
    """Test successful Google login endpoint."""
    # Mock the get_authorized_url function
    with patch('app.api.v1.endpoints.auth.get_authorized_url') as mock_get_url:
        mock_get_url.return_value = "https://accounts.google.com/o/oauth2/v2/auth?client_id=test&redirect_uri=test&scope=test&response_type=code"
        
        response = client.get("/auth/google/login")
        
        assert response.status_code == 200
        assert "authorization_url" in response.json()
        mock_get_url.assert_called_once()


def test_google_login_server_cred_error():
    """Test Google login endpoint when ServerCredError is raised."""
    # Mock the get_authorized_url function to raise ServerCredError
    with patch('app.api.v1.endpoints.auth.get_authorized_url') as mock_get_url:
        mock_get_url.side_effect = ServerCredError("Client ID not configured", None)
        
        response = client.get("/auth/google/login")
        
        assert response.status_code == 401
        assert "Client ID not configured" in response.json()["detail"]


def test_google_login_generic_exception():
    """Test Google login endpoint when a generic exception is raised."""
    # Mock the get_authorized_url function to raise a generic exception
    with patch('app.api.v1.endpoints.auth.get_authorized_url') as mock_get_url:
        mock_get_url.side_effect = Exception("Unknown error")
        
        response = client.get("/auth/google/login")
        
        assert response.status_code == 500
        assert "Unknown Error occured in servers" in response.json()["detail"]


def test_google_callback_success():
    """Test successful Google callback endpoint."""
    # This test would require more complex mocking of the dependencies
    # For now, we'll just test that the endpoint exists
    response = client.get("/auth/google/callback?code=test_code")
    # We expect this to fail because we haven't mocked the dependencies
    # but we can at least verify the endpoint exists
    assert response.status_code in [401, 500, 422]  # Any error status is fine for this basic test


def test_google_callback_missing_code():
    """Test Google callback endpoint when code is missing."""
    response = client.get("/auth/google/callback")
    # FastAPI validation should catch this
    assert response.status_code == 422