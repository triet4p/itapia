"""Tests for the profiles CRUD module."""

import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.crud.profiles import get_by_id, get_by_name, get_multi_by_user, create, update, remove


def test_get_by_id_success():
    """Test successful profile retrieval by ID."""
    # Mock database session
    mock_session = Mock(spec=Session)
    
    # Mock the execute result
    mock_result = Mock()
    mock_row = {
        "profile_id": "profile123",
        "user_id": "user123",
        "profile_name": "Test Profile",
        "description": "A test profile",
        "risk_tolerance": '{"level": "moderate"}',
        "invest_goal": '{"goal": "growth"}',
        "knowledge_exp": '{"level": "intermediate"}',
        "capital_income": '{"amount": 5000}',
        "personal_prefer": '{"preference": "balanced"}',
        "use_in_advisor": True,
        "is_default": False,
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }
    mock_result.mappings.return_value.first.return_value = mock_row
    mock_session.execute.return_value = mock_result
    
    # Test the function
    result = get_by_id(mock_session, profile_id="profile123")
    
    # Assertions
    assert result == mock_row
    mock_session.execute.assert_called_once()
    # Check that the query contains the correct parameters
    call_args = mock_session.execute.call_args
    assert call_args[0][0].text == text("SELECT * FROM investment_profiles WHERE profile_id = :profile_id").text
    assert call_args[1]["profile_id"] == "profile123"


def test_get_by_id_not_found():
    """Test profile retrieval by ID when profile is not found."""
    # Mock database session
    mock_session = Mock(spec=Session)
    
    # Mock the execute result to return None
    mock_result = Mock()
    mock_result.mappings.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result
    
    # Test the function
    result = get_by_id(mock_session, profile_id="nonexistent_profile")
    
    # Assertions
    assert result is None


def test_get_by_name_success():
    """Test successful profile retrieval by name."""
    # Mock database session
    mock_session = Mock(spec=Session)
    
    # Mock the execute result
    mock_result = Mock()
    mock_row = {
        "profile_id": "profile123",
        "user_id": "user123",
        "profile_name": "Test Profile",
        "description": "A test profile",
        "risk_tolerance": '{"level": "moderate"}',
        "invest_goal": '{"goal": "growth"}',
        "knowledge_exp": '{"level": "intermediate"}',
        "capital_income": '{"amount": 5000}',
        "personal_prefer": '{"preference": "balanced"}',
        "use_in_advisor": True,
        "is_default": False,
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }
    mock_result.mappings.return_value.first.return_value = mock_row
    mock_session.execute.return_value = mock_result
    
    # Test the function
    result = get_by_name(mock_session, profile_name="Test Profile", user_id="user123")
    
    # Assertions
    assert result == mock_row
    mock_session.execute.assert_called_once()
    # Check that the query contains the correct parameters
    call_args = mock_session.execute.call_args
    assert "SELECT * FROM investment_profiles WHERE profile_name = :profile_name AND user_id = :user_id" in call_args[0][0].text
    assert call_args[1]["profile_name"] == "Test Profile"
    assert call_args[1]["user_id"] == "user123"


def test_get_multi_by_user_success():
    """Test successful retrieval of multiple profiles for a user."""
    # Mock database session
    mock_session = Mock(spec=Session)
    
    # Mock the execute result
    mock_result = Mock()
    mock_rows = [
        {
            "profile_id": "profile123",
            "user_id": "user123",
            "profile_name": "Test Profile 1",
            "description": "A test profile",
            "risk_tolerance": '{"level": "moderate"}',
            "invest_goal": '{"goal": "growth"}',
            "knowledge_exp": '{"level": "intermediate"}',
            "capital_income": '{"amount": 5000}',
            "personal_prefer": '{"preference": "balanced"}',
            "use_in_advisor": True,
            "is_default": False,
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        },
        {
            "profile_id": "profile456",
            "user_id": "user123",
            "profile_name": "Test Profile 2",
            "description": "Another test profile",
            "risk_tolerance": '{"level": "aggressive"}',
            "invest_goal": '{"goal": "income"}',
            "knowledge_exp": '{"level": "advanced"}',
            "capital_income": '{"amount": 10000}',
            "personal_prefer": '{"preference": "growth"}',
            "use_in_advisor": True,
            "is_default": True,
            "created_at": "2023-01-02T00:00:00",
            "updated_at": "2023-01-02T00:00:00"
        }
    ]
    mock_result.mappings.return_value.all.return_value = mock_rows
    mock_session.execute.return_value = mock_result
    
    # Test the function
    result = get_multi_by_user(mock_session, user_id="user123")
    
    # Assertions
    assert result == mock_rows
    mock_session.execute.assert_called_once()
    # Check that the query contains the correct parameters
    call_args = mock_session.execute.call_args
    assert "SELECT * FROM investment_profiles WHERE user_id = :user_id ORDER BY created_at DESC" in call_args[0][0].text
    assert call_args[1]["user_id"] == "user123"


def test_create_profile_success():
    """Test successful profile creation."""
    # Mock database session
    mock_session = Mock(spec=Session)
    
    # Mock the execute result
    mock_result = Mock()
    mock_row = {
        "profile_id": "newprofile123",
        "user_id": "user123",
        "profile_name": "New Test Profile",
        "description": "A new test profile",
        "risk_tolerance": '{"level": "moderate"}',
        "invest_goal": '{"goal": "growth"}',
        "knowledge_exp": '{"level": "intermediate"}',
        "capital_income": '{"amount": 5000}',
        "personal_prefer": '{"preference": "balanced"}',
        "use_in_advisor": True,
        "is_default": False,
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }
    mock_result.mappings.return_value.first.return_value = mock_row
    mock_session.execute.return_value = mock_result
    
    # Mock profile data
    profile_data = {
        "profile_id": "newprofile123",
        "user_id": "user123",
        "profile_name": "New Test Profile",
        "description": "A new test profile",
        "risk_tolerance": '{"level": "moderate"}',
        "invest_goal": '{"goal": "growth"}',
        "knowledge_exp": '{"level": "intermediate"}',
        "capital_income": '{"amount": 5000}',
        "personal_prefer": '{"preference": "balanced"}',
        "use_in_advisor": True,
        "is_default": False
    }
    
    # Test the function
    result = create(mock_session, profile_data=profile_data)
    
    # Assertions
    assert result == mock_row
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()
    # Check that the query contains the correct parameters
    call_args = mock_session.execute.call_args
    assert "INSERT INTO investment_profiles" in call_args[0][0].text
    assert call_args[1] == profile_data


def test_update_profile_success():
    """Test successful profile update."""
    # Mock database session
    mock_session = Mock(spec=Session)
    
    # Mock the execute result
    mock_result = Mock()
    mock_row = {
        "profile_id": "profile123",
        "user_id": "user123",
        "profile_name": "Updated Test Profile",
        "description": "An updated test profile",
        "risk_tolerance": '{"level": "aggressive"}',
        "invest_goal": '{"goal": "income"}',
        "knowledge_exp": '{"level": "advanced"}',
        "capital_income": '{"amount": 10000}',
        "personal_prefer": '{"preference": "growth"}',
        "use_in_advisor": True,
        "is_default": False,
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-02T00:00:00"
    }
    mock_result.mappings.return_value.first.return_value = mock_row
    mock_session.execute.return_value = mock_result
    
    # Mock update data
    update_data = {
        "profile_name": "Updated Test Profile",
        "description": "An updated test profile"
    }
    
    # Test the function
    result = update(mock_session, profile_id="profile123", update_data=update_data)
    
    # Assertions
    assert result == mock_row
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()
    # Check that the query contains the correct parameters
    call_args = mock_session.execute.call_args
    assert "UPDATE investment_profiles" in call_args[0][0].text
    assert call_args[1]["profile_id"] == "profile123"
    assert call_args[1]["profile_name"] == "Updated Test Profile"
    assert call_args[1]["description"] == "An updated test profile"
    assert "updated_at = NOW()" in call_args[0][0].text


def test_remove_profile_success():
    """Test successful profile removal."""
    # Mock database session
    mock_session = Mock(spec=Session)
    
    # Mock the execute result
    mock_result = Mock()
    mock_row = {
        "profile_id": "profile123",
        "user_id": "user123",
        "profile_name": "Test Profile",
        "description": "A test profile",
        "risk_tolerance": '{"level": "moderate"}',
        "invest_goal": '{"goal": "growth"}',
        "knowledge_exp": '{"level": "intermediate"}',
        "capital_income": '{"amount": 5000}',
        "personal_prefer": '{"preference": "balanced"}',
        "use_in_advisor": True,
        "is_default": False,
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }
    mock_result.mappings.return_value.first.return_value = mock_row
    mock_session.execute.return_value = mock_result
    
    # Test the function
    result = remove(mock_session, profile_id="profile123")
    
    # Assertions
    assert result == mock_row
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()
    # Check that the query contains the correct parameters
    call_args = mock_session.execute.call_args
    assert "DELETE FROM investment_profiles WHERE profile_id = :profile_id" in call_args[0][0].text
    assert call_args[1]["profile_id"] == "profile123"