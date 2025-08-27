"""Tests for the root endpoint."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_read_root():
    """Test the root endpoint returns the correct response."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to ITAPIA API Service"}


def test_read_root_with_different_method():
    """Test that the root endpoint only accepts GET requests."""
    response = client.post("/")
    # FastAPI will return 405 Method Not Allowed for POST to a GET-only endpoint
    assert response.status_code == 405