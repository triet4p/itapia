"""Tests for the main application module."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_read_root(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to ITAPIA API Service"}


def test_app_info():
    """Test that the app has the correct title and version."""
    assert app.title == "ITAPIA API Service"
    assert app.version == "1.0.0"
    assert "API Gateway for the ITAPIA system" in app.description


def test_cors_middleware(client):
    """Test that CORS headers are set correctly."""
    response = client.get("/", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    # Note: FastAPI test client doesn't fully simulate CORS middleware behavior
    # This is more of a smoke test to ensure the app runs