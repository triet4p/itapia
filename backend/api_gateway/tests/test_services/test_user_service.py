"""Tests for the user service."""

from unittest.mock import Mock

import pytest
from app.core.exceptions import DBError, NoDataError
from app.services.users import UserService
from itapia_common.schemas.entities.users import UserCreate, UserEntity
from sqlalchemy.orm import Session


def test_user_service_init():
    """Test UserService initialization."""
    mock_session = Mock(spec=Session)
    service = UserService(mock_session)
    assert service.rdbms_session == mock_session


def test_create_user_success():
    """Test successful user creation."""
    # Mock database session
    mock_session = Mock(spec=Session)

    # Mock the create function return value
    mock_row = {
        "user_id": "user123",
        "email": "test@example.com",
        "full_name": "Test User",
        "avatar_url": "http://example.com/avatar.jpg",
        "google_id": "google123",
        "is_active": True,
    }
    mock_session.execute.return_value.mappings.return_value.first.return_value = (
        mock_row
    )

    # Create service
    service = UserService(mock_session)

    # Create user data
    user_data = UserCreate(
        email="test@example.com",
        full_name="Test User",
        avatar_url="http://example.com/avatar.jpg",
        google_id="google123",
    )

    # Test user creation
    result = service.create_user(user_data)

    # Assertions
    assert isinstance(result, UserEntity)
    assert result.user_id == "user123"
    assert result.email == "test@example.com"
    assert result.is_active is True


def test_create_user_failure():
    """Test user creation failure."""
    # Mock database session
    mock_session = Mock(spec=Session)

    # Mock the create function to return None
    mock_session.execute.return_value.mappings.return_value.first.return_value = None

    # Create service
    service = UserService(mock_session)

    # Create user data
    user_data = UserCreate(
        email="test@example.com",
        full_name="Test User",
        avatar_url="http://example.com/avatar.jpg",
        google_id="google123",
    )

    # Test user creation and expect DBError
    with pytest.raises(DBError) as exc_info:
        service.create_user(user_data)

    assert "Can not create user" in str(exc_info.value.msg)


def test_get_user_by_google_id_success():
    """Test successful user retrieval by Google ID."""
    # Mock database session
    mock_session = Mock(spec=Session)

    # Mock the get_by_google_id function return value
    mock_row = {
        "user_id": "user123",
        "email": "test@example.com",
        "full_name": "Test User",
        "avatar_url": "http://example.com/avatar.jpg",
        "google_id": "google123",
        "is_active": True,
    }
    # Patch the actual function
    with pytest.MonkeyPatch().context() as m:
        m.setattr(
            "app.services.users.get_by_google_id", lambda session, google_id: mock_row
        )

        # Create service
        service = UserService(mock_session)

        # Test user retrieval
        result = service.get_user_by_google_id("google123")

        # Assertions
        assert isinstance(result, UserEntity)
        assert result.google_id == "google123"
        assert result.email == "test@example.com"


def test_get_user_by_google_id_not_found():
    """Test user retrieval by Google ID when user is not found."""
    # Mock database session
    mock_session = Mock(spec=Session)

    # Patch the actual function to return None
    with pytest.MonkeyPatch().context() as m:
        m.setattr(
            "app.services.users.get_by_google_id", lambda session, google_id: None
        )

        # Create service
        service = UserService(mock_session)

        # Test user retrieval and expect NoDataError
        with pytest.raises(NoDataError) as exc_info:
            service.get_user_by_google_id("nonexistent_google_id")

        assert "Not found user with google id" in str(exc_info.value.msg)


def test_get_user_by_id_success():
    """Test successful user retrieval by user ID."""
    # Mock database session
    mock_session = Mock(spec=Session)

    # Mock the get_by_id function return value
    mock_row = {
        "user_id": "user123",
        "email": "test@example.com",
        "full_name": "Test User",
        "avatar_url": "http://example.com/avatar.jpg",
        "google_id": "google123",
        "is_active": True,
    }

    # Patch the actual function
    with pytest.MonkeyPatch().context() as m:
        m.setattr("app.services.users.get_by_id", lambda session, user_id: mock_row)

        # Create service
        service = UserService(mock_session)

        # Test user retrieval
        result = service.get_user_by_id("user123")

        # Assertions
        assert isinstance(result, UserEntity)
        assert result.user_id == "user123"
        assert result.email == "test@example.com"


def test_get_user_by_id_not_found():
    """Test user retrieval by user ID when user is not found."""
    # Mock database session
    mock_session = Mock(spec=Session)

    # Patch the actual function to return None
    with pytest.MonkeyPatch().context() as m:
        m.setattr("app.services.users.get_by_id", lambda session, user_id: None)

        # Create service
        service = UserService(mock_session)

        # Test user retrieval and expect NoDataError
        with pytest.raises(NoDataError) as exc_info:
            service.get_user_by_id("nonexistent_user_id")

        assert "Not found user with id" in str(exc_info.value.msg)


def test_get_or_create_user_exists():
    """Test get_or_create when user already exists."""
    # Mock database session
    mock_session = Mock(spec=Session)

    # Mock the get_by_google_id function return value
    mock_row = {
        "user_id": "user123",
        "email": "test@example.com",
        "full_name": "Test User",
        "avatar_url": "http://example.com/avatar.jpg",
        "google_id": "google123",
        "is_active": True,
    }

    # Patch the actual function
    with pytest.MonkeyPatch().context() as m:
        m.setattr(
            "app.services.users.get_by_google_id", lambda session, google_id: mock_row
        )

        # Create service
        service = UserService(mock_session)

        # Create user data
        user_data = UserCreate(
            email="test@example.com",
            full_name="Test User",
            avatar_url="http://example.com/avatar.jpg",
            google_id="google123",
        )

        # Test get_or_create
        result = service.get_or_create(user_data)

        # Assertions
        assert isinstance(result, UserEntity)
        assert result.user_id == "user123"
        assert result.google_id == "google123"


def test_get_or_create_user_new():
    """Test get_or_create when user needs to be created."""
    # Mock database session
    mock_session = Mock(spec=Session)

    # Mock the get_by_google_id function to return None (user not found)
    # Mock the create function return value
    mock_row = {
        "user_id": "newuser123",
        "email": "newtest@example.com",
        "full_name": "New Test User",
        "avatar_url": "http://example.com/newavatar.jpg",
        "google_id": "newgoogle123",
        "is_active": True,
    }

    # Track if create was called
    create_called = False

    def mock_get_by_google_id(session, google_id):
        return None

    def mock_create(session, user_data):
        nonlocal create_called
        create_called = True
        return mock_row

    # Patch the actual functions
    with pytest.MonkeyPatch().context() as m:
        m.setattr("app.services.users.get_by_google_id", mock_get_by_google_id)
        m.setattr("app.services.users.create", mock_create)

        # Create service
        service = UserService(mock_session)

        # Create user data
        user_data = UserCreate(
            email="newtest@example.com",
            full_name="New Test User",
            avatar_url="http://example.com/newavatar.jpg",
            google_id="newgoogle123",
        )

        # Test get_or_create
        result = service.get_or_create(user_data)

        # Assertions
        assert isinstance(result, UserEntity)
        assert result.user_id == "newuser123"
        assert result.google_id == "newgoogle123"
        assert create_called is True
