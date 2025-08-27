"""Tests for the profiles endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock

from app.main import app

client = TestClient(app)


def test_create_user_profile_unauthorized():
    """Test that creating a profile requires authentication."""
    response = client.post("/profiles", json={
        "profile_name": "Test Profile",
        "description": "A test profile"
    })
    # Should return authentication error
    assert response.status_code in [401, 403, 422]


def test_get_user_profiles_unauthorized():
    """Test that getting profiles requires authentication."""
    response = client.get("/profiles")
    # Should return authentication error
    assert response.status_code in [401, 403, 422]


def test_get_user_profile_details_unauthorized():
    """Test that getting a specific profile requires authentication."""
    response = client.get("/profiles/test_profile_id")
    # Should return authentication error
    assert response.status_code in [401, 403, 422]


def test_update_user_profile_unauthorized():
    """Test that updating a profile requires authentication."""
    response = client.put("/profiles/test_profile_id", json={
        "profile_name": "Updated Profile"
    })
    # Should return authentication error
    assert response.status_code in [401, 403, 422]


def test_delete_user_profile_unauthorized():
    """Test that deleting a profile requires authentication."""
    response = client.delete("/profiles/test_profile_id")
    # Should return authentication error
    assert response.status_code in [401, 403, 422]