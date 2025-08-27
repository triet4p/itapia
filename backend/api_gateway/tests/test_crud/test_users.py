"""Tests for the users CRUD module."""

import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.crud.users import get_by_google_id, get_by_id, create


def test_get_by_google_id_success():
    """Test successful user retrieval by Google ID."""
    # Mock database session
    mock_session = Mock(spec=Session)
    
    # Mock the execute result
    mock_result = Mock()
    mock_row = {
        "user_id": "user123",
        "email": "test@example.com",
        "full_name": "Test User",
        "avatar_url": "http://example.com/avatar.jpg",
        "google_id": "google123",
        "is_active": True
    }
    mock_result.mappings.return_value.first.return_value = mock_row
    mock_session.execute.return_value = mock_result
    
    # Test the function
    result = get_by_google_id(mock_session, "google123")
    
    # Assertions
    assert result == mock_row
    mock_session.execute.assert_called_once()
    # Check that the query contains the correct parameters
    call_args = mock_session.execute.call_args
    assert call_args[0][0].text == text("SELECT * FROM users WHERE google_id = :google_id and is_active=true").text
    assert call_args[1]["google_id"] == "google123"


def test_get_by_google_id_not_found():
    """Test user retrieval by Google ID when user is not found."""
    # Mock database session
    mock_session = Mock(spec=Session)
    
    # Mock the execute result to return None
    mock_result = Mock()
    mock_result.mappings.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result
    
    # Test the function
    result = get_by_google_id(mock_session, "nonexistent_google_id")
    
    # Assertions
    assert result is None


def test_get_by_id_success():
    """Test successful user retrieval by user ID."""
    # Mock database session
    mock_session = Mock(spec=Session)
    
    # Mock the execute result
    mock_result = Mock()
    mock_row = {
        "user_id": "user123",
        "email": "test@example.com",
        "full_name": "Test User",
        "avatar_url": "http://example.com/avatar.jpg",
        "google_id": "google123",
        "is_active": True
    }
    mock_result.mappings.return_value.first.return_value = mock_row
    mock_session.execute.return_value = mock_result
    
    # Test the function
    result = get_by_id(mock_session, "user123")
    
    # Assertions
    assert result == mock_row
    mock_session.execute.assert_called_once()
    # Check that the query contains the correct parameters
    call_args = mock_session.execute.call_args
    assert call_args[0][0].text == text("SELECT * FROM users WHERE user_id = :user_id and is_active=true").text
    assert call_args[1]["user_id"] == "user123"


def test_get_by_id_not_found():
    """Test user retrieval by user ID when user is not found."""
    # Mock database session
    mock_session = Mock(spec=Session)
    
    # Mock the execute result to return None
    mock_result = Mock()
    mock_result.mappings.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result
    
    # Test the function
    result = get_by_id(mock_session, "nonexistent_user_id")
    
    # Assertions
    assert result is None


def test_create_user_success():
    """Test successful user creation."""
    # Mock database session
    mock_session = Mock(spec=Session)
    
    # Mock the execute result
    mock_result = Mock()
    mock_row = {
        "user_id": "newuser123",
        "email": "newtest@example.com",
        "full_name": "New Test User",
        "avatar_url": "http://example.com/newavatar.jpg",
        "google_id": "newgoogle123",
        "is_active": True
    }
    mock_result.mappings.return_value.first.return_value = mock_row
    mock_session.execute.return_value = mock_result
    
    # Mock user data
    user_data = {
        "user_id": "newuser123",
        "email": "newtest@example.com",
        "full_name": "New Test User",
        "avatar_url": "http://example.com/newavatar.jpg",
        "google_id": "newgoogle123",
        "is_active": True
    }
    
    # Test the function
    result = create(mock_session, user_data)
    
    # Assertions
    assert result == mock_row
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()
    # Check that the query contains the correct parameters
    call_args = mock_session.execute.call_args
    assert "INSERT INTO users" in call_args[0][0].text
    assert call_args[1] == user_data