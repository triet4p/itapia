"""Tests for the auth service."""

from unittest.mock import Mock, patch

import pytest
from app.core.exceptions import AuthError, ServerCredError
from app.services.auth._service import get_current_user
from app.services.auth.security import create_access_token, verify_access_token
from app.services.users import UserService
from itapia_common.schemas.entities.users import UserEntity


def test_get_current_user_success():
    """Test successful user authentication."""
    # Mock user service
    mock_user_service = Mock(spec=UserService)

    # Mock token verification
    with patch("app.services.auth._service.verify_access_token") as mock_verify:
        # Mock token payload
        mock_payload = {"sub": "user123"}
        mock_verify.return_value = mock_payload

        # Mock user entity
        mock_user = UserEntity(
            user_id="user123",
            email="test@example.com",
            full_name="Test User",
            avatar_url="http://example.com/avatar.jpg",
            google_id="google123",
            is_active=True,
        )
        mock_user_service.get_user_by_id.return_value = mock_user

        # Test the function
        result = get_current_user(mock_user_service, "valid_token")

        # Assertions
        assert isinstance(result, UserEntity)
        assert result.user_id == "user123"
        assert result.email == "test@example.com"
        mock_verify.assert_called_once_with("valid_token")
        mock_user_service.get_user_by_id.assert_called_once_with("user123")


def test_get_current_user_invalid_token_payload():
    """Test authentication with invalid token payload."""
    # Mock user service
    mock_user_service = Mock(spec=UserService)

    # Mock token verification
    with patch("app.services.auth._service.verify_access_token") as mock_verify:
        # Mock token payload with None sub
        mock_payload = {"sub": None}
        mock_verify.return_value = mock_payload

        # Test the function and expect AuthError
        with pytest.raises(AuthError) as exc_info:
            get_current_user(mock_user_service, "invalid_token")

        assert "Invalid token payload" in str(exc_info.value.msg)


def test_get_current_user_token_verification_failure():
    """Test authentication when token verification fails."""
    # Mock user service
    mock_user_service = Mock(spec=UserService)

    # Mock token verification to raise an exception
    with patch("app.services.auth._service.verify_access_token") as mock_verify:
        mock_verify.side_effect = Exception("Token verification failed")

        # Test the function and expect AuthError
        with pytest.raises(AuthError) as exc_info:
            get_current_user(mock_user_service, "invalid_token")

        assert "Could not validate credentials" in str(exc_info.value.msg)


def test_get_current_user_user_not_found():
    """Test authentication when user is not found."""
    # Mock user service
    mock_user_service = Mock(spec=UserService)

    # Mock token verification
    with patch("app.services.auth._service.verify_access_token") as mock_verify:
        # Mock token payload
        mock_payload = {"sub": "nonexistent_user"}
        mock_verify.return_value = mock_payload

        # Mock user service to raise NoDataError
        mock_user_service.get_user_by_id.side_effect = Exception("User not found")

        # Test the function and expect AuthError
        with pytest.raises(AuthError) as exc_info:
            get_current_user(mock_user_service, "valid_token")

        assert "Could not validate credentials" in str(exc_info.value.msg)


def test_create_access_token():
    """Test creating an access token."""
    token = create_access_token("user123")
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_access_token_with_expiration():
    """Test creating an access token with custom expiration."""
    from datetime import timedelta

    token = create_access_token("user123", timedelta(minutes=60))
    assert isinstance(token, str)
    assert len(token) > 0


def test_verify_access_token_valid():
    """Test verifying a valid access token."""
    # Create a token
    token = create_access_token("user123")

    # Verify the token
    payload = verify_access_token(token)

    # Check payload
    assert "sub" in payload
    assert payload["sub"] == "user123"
    assert "exp" in payload


def test_verify_access_token_invalid():
    """Test verifying an invalid access token."""
    with pytest.raises(ServerCredError) as exc_info:
        verify_access_token("invalid_token")

    assert "Could not validate credentials" in exc_info.value.detail
