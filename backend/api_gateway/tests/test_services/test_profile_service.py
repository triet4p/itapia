"""Tests for the profile service."""

import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.services.profiles import ProfileService
from app.core.exceptions import NoDataError, AuthError, DBError

from itapia_common.schemas.entities.profiles import ProfileCreate, ProfileUpdate, ProfileEntity


class MockProfileData(BaseModel):
    """Mock profile data for testing."""
    name: str
    value: dict


def test_profile_service_init():
    """Test ProfileService initialization."""
    mock_session = Mock(spec=Session)
    service = ProfileService(mock_session)
    assert service.db == mock_session


def test_convert_parts_to_json_string():
    """Test the _convert_parts_to_json_string helper method."""
    mock_session = Mock(spec=Session)
    service = ProfileService(mock_session)
    
    # Create mock data
    mock_data = MockProfileData(
        name="test",
        value={"nested": "data"}
    )
    
    # Test conversion
    result = service._convert_parts_to_json_string(mock_data)
    
    # Assertions
    assert isinstance(result, dict)
    assert "name" in result
    assert "value" in result
    assert isinstance(result["value"], str)  # Should be JSON string


def test_get_profile_by_id_success():
    """Test successful profile retrieval by ID."""
    # Mock database session
    mock_session = Mock(spec=Session)
    
    # Mock the CRUD function return value
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
    
    # Patch the actual CRUD function
    with pytest.MonkeyPatch().context() as m:
        m.setattr("app.services.profiles.profile_crud.get_by_id", lambda db, profile_id: mock_row)
        
        # Create service
        service = ProfileService(mock_session)
        
        # Test profile retrieval
        result = service.get_profile_by_id(profile_id="profile123", user_id="user123")
        
        # Assertions
        assert isinstance(result, ProfileEntity)
        assert result.profile_id == "profile123"
        assert result.user_id == "user123"


def test_get_profile_by_id_not_found():
    """Test profile retrieval by ID when profile is not found."""
    # Mock database session
    mock_session = Mock(spec=Session)
    
    # Patch the actual CRUD function to return None
    with pytest.MonkeyPatch().context() as m:
        m.setattr("app.services.profiles.profile_crud.get_by_id", lambda db, profile_id: None)
        
        # Create service
        service = ProfileService(mock_session)
        
        # Test profile retrieval and expect NoDataError
        with pytest.raises(NoDataError) as exc_info:
            service.get_profile_by_id(profile_id="nonexistent_profile", user_id="user123")
        
        assert "Not found profile with id" in str(exc_info.value.msg)


def test_get_profile_by_id_unauthorized():
    """Test profile retrieval by ID when user is not authorized."""
    # Mock database session
    mock_session = Mock(spec=Session)
    
    # Mock the CRUD function return value with different user_id
    mock_row = {
        "profile_id": "profile123",
        "user_id": "different_user",
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
    
    # Patch the actual CRUD function
    with pytest.MonkeyPatch().context() as m:
        m.setattr("app.services.profiles.profile_crud.get_by_id", lambda db, profile_id: mock_row)
        
        # Create service
        service = ProfileService(mock_session)
        
        # Test profile retrieval and expect AuthError
        with pytest.raises(AuthError) as exc_info:
            service.get_profile_by_id(profile_id="profile123", user_id="user123")
        
        assert "can not accessed by user" in str(exc_info.value.msg)


def test_get_profiles_by_user():
    """Test retrieving all profiles for a user."""
    # Mock database session
    mock_session = Mock(spec=Session)
    
    # Mock the CRUD function return value
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
    
    # Patch the actual CRUD function
    with pytest.MonkeyPatch().context() as m:
        m.setattr("app.services.profiles.profile_crud.get_multi_by_user", lambda db, user_id: mock_rows)
        
        # Create service
        service = ProfileService(mock_session)
        
        # Test profile retrieval
        result = service.get_profiles_by_user(user_id="user123")
        
        # Assertions
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(profile, ProfileEntity) for profile in result)
        assert result[0].profile_id == "profile123"
        assert result[1].profile_id == "profile456"


def test_create_profile_success():
    """Test successful profile creation."""
    # Mock database session
    mock_session = Mock(spec=Session)
    
    # Mock the CRUD function return value
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
    
    # Track if create was called
    create_called = False
    create_data = None
    
    def mock_create(db, profile_data):
        nonlocal create_called, create_data
        create_called = True
        create_data = profile_data
        return mock_row
    
    # Patch the actual CRUD function
    with pytest.MonkeyPatch().context() as m:
        m.setattr("app.services.profiles.profile_crud.create", mock_create)
        
        # Create service
        service = ProfileService(mock_session)
        
        # Create profile data
        profile_data = ProfileCreate(
            profile_name="New Test Profile",
            description="A new test profile",
            risk_tolerance={"level": "moderate"},
            invest_goal={"goal": "growth"},
            knowledge_exp={"level": "intermediate"},
            capital_income={"amount": 5000},
            personal_prefer={"preference": "balanced"},
            use_in_advisor=True,
            is_default=False
        )
        
        # Test profile creation
        result = service.create_profile(profile_in=profile_data, user_id="user123")
        
        # Assertions
        assert isinstance(result, ProfileEntity)
        assert result.profile_id == "newprofile123"
        assert create_called is True
        assert create_data is not None
        assert create_data["user_id"] == "user123"
        assert "profile_id" in create_data


def test_create_profile_failure():
    """Test profile creation failure."""
    # Mock database session
    mock_session = Mock(spec=Session)
    
    # Patch the actual CRUD function to return None
    with pytest.MonkeyPatch().context() as m:
        m.setattr("app.services.profiles.profile_crud.create", lambda db, profile_data: None)
        
        # Create service
        service = ProfileService(mock_session)
        
        # Create profile data
        profile_data = ProfileCreate(
            profile_name="New Test Profile",
            description="A new test profile",
            risk_tolerance={"level": "moderate"},
            invest_goal={"goal": "growth"},
            knowledge_exp={"level": "intermediate"},
            capital_income={"amount": 5000},
            personal_prefer={"preference": "balanced"},
            use_in_advisor=True,
            is_default=False
        )
        
        # Test profile creation and expect DBError
        with pytest.raises(DBError) as exc_info:
            service.create_profile(profile_in=profile_data, user_id="user123")
        
        assert "Failed to create profile" in str(exc_info.value.msg)


def test_update_profile_success():
    """Test successful profile update."""
    # Mock database session
    mock_session = Mock(spec=Session)
    
    # Mock the get_profile_by_id return value
    mock_profile_entity = ProfileEntity(
        profile_id="profile123",
        user_id="user123",
        profile_name="Test Profile",
        description="A test profile",
        risk_tolerance={"level": "moderate"},
        invest_goal={"goal": "growth"},
        knowledge_exp={"level": "intermediate"},
        capital_income={"amount": 5000},
        personal_prefer={"preference": "balanced"},
        use_in_advisor=True,
        is_default=False,
        created_at="2023-01-01T00:00:00",
        updated_at="2023-01-01T00:00:00"
    )
    
    # Mock the CRUD update function return value
    mock_updated_row = {
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
    
    # Track if update was called
    update_called = False
    update_data = None
    
    def mock_get_profile_by_id(profile_id, user_id):
        return mock_profile_entity
    
    def mock_update(db, profile_id, update_data_param):
        nonlocal update_called, update_data
        update_called = True
        update_data = update_data_param
        return mock_updated_row
    
    # Patch the actual functions
    with pytest.MonkeyPatch().context() as m:
        m.setattr(service, "get_profile_by_id", mock_get_profile_by_id)
        m.setattr("app.services.profiles.profile_crud.update", mock_update)
        
        # Create service
        service = ProfileService(mock_session)
        
        # Create update data
        update_data = ProfileUpdate(
            profile_name="Updated Test Profile",
            description="An updated test profile"
        )
        
        # Test profile update
        result = service.update_profile(
            profile_id="profile123",
            user_id="user123",
            profile_in=update_data
        )
        
        # Assertions
        assert isinstance(result, ProfileEntity)
        assert result.profile_name == "Updated Test Profile"
        assert update_called is True
        assert update_data is not None


def test_update_profile_no_changes():
    """Test profile update with no changes."""
    # Mock database session
    mock_session = Mock(spec=Session)
    
    # Mock the get_profile_by_id return value
    mock_profile_entity = ProfileEntity(
        profile_id="profile123",
        user_id="user123",
        profile_name="Test Profile",
        description="A test profile",
        risk_tolerance={"level": "moderate"},
        invest_goal={"goal": "growth"},
        knowledge_exp={"level": "intermediate"},
        capital_income={"amount": 5000},
        personal_prefer={"preference": "balanced"},
        use_in_advisor=True,
        is_default=False,
        created_at="2023-01-01T00:00:00",
        updated_at="2023-01-01T00:00:00"
    )
    
    # Track if update was called
    update_called = False
    
    def mock_get_profile_by_id(profile_id, user_id):
        return mock_profile_entity
    
    def mock_update(db, profile_id, update_data):
        nonlocal update_called
        update_called = True
        return None  # This shouldn't be reached
    
    def mock_convert_parts_to_json_string(data):
        return {}  # Return empty dict to simulate no changes
    
    # Patch the actual functions
    with pytest.MonkeyPatch().context() as m:
        m.setattr(service, "get_profile_by_id", mock_get_profile_by_id)
        m.setattr("app.services.profiles.profile_crud.update", mock_update)
        m.setattr(service, "_convert_parts_to_json_string", mock_convert_parts_to_json_string)
        
        # Create service
        service = ProfileService(mock_session)
        
        # Create empty update data
        update_data = ProfileUpdate()
        
        # Test profile update
        result = service.update_profile(
            profile_id="profile123",
            user_id="user123",
            profile_in=update_data
        )
        
        # Assertions
        assert isinstance(result, ProfileEntity)
        assert result.profile_id == "profile123"
        assert update_called is False  # Update shouldn't be called when there are no changes


def test_remove_profile_success():
    """Test successful profile removal."""
    # Mock database session
    mock_session = Mock(spec=Session)
    
    # Mock the get_profile_by_id return value
    mock_profile_entity = ProfileEntity(
        profile_id="profile123",
        user_id="user123",
        profile_name="Test Profile",
        description="A test profile",
        risk_tolerance={"level": "moderate"},
        invest_goal={"goal": "growth"},
        knowledge_exp={"level": "intermediate"},
        capital_income={"amount": 5000},
        personal_prefer={"preference": "balanced"},
        use_in_advisor=True,
        is_default=False,
        created_at="2023-01-01T00:00:00",
        updated_at="2023-01-01T00:00:00"
    )
    
    # Mock the CRUD remove function return value
    mock_deleted_row = {
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
    
    # Track if remove was called
    remove_called = False
    
    def mock_get_profile_by_id(profile_id, user_id):
        return mock_profile_entity
    
    def mock_remove(db, profile_id):
        nonlocal remove_called
        remove_called = True
        return mock_deleted_row
    
    # Patch the actual functions
    with pytest.MonkeyPatch().context() as m:
        m.setattr(service, "get_profile_by_id", mock_get_profile_by_id)
        m.setattr("app.services.profiles.profile_crud.remove", mock_remove)
        
        # Create service
        service = ProfileService(mock_session)
        
        # Test profile removal
        result = service.remove_profile(profile_id="profile123", user_id="user123")
        
        # Assertions
        assert isinstance(result, ProfileEntity)
        assert result.profile_id == "profile123"
        assert remove_called is True


def test_remove_profile_failure():
    """Test profile removal failure."""
    # Mock database session
    mock_session = Mock(spec=Session)
    
    # Mock the get_profile_by_id return value
    mock_profile_entity = ProfileEntity(
        profile_id="profile123",
        user_id="user123",
        profile_name="Test Profile",
        description="A test profile",
        risk_tolerance={"level": "moderate"},
        invest_goal={"goal": "growth"},
        knowledge_exp={"level": "intermediate"},
        capital_income={"amount": 5000},
        personal_prefer={"preference": "balanced"},
        use_in_advisor=True,
        is_default=False,
        created_at="2023-01-01T00:00:00",
        updated_at="2023-01-01T00:00:00"
    )
    
    # Patch the actual functions
    with pytest.MonkeyPatch().context() as m:
        m.setattr(service, "get_profile_by_id", lambda profile_id, user_id: mock_profile_entity)
        m.setattr("app.services.profiles.profile_crud.remove", lambda db, profile_id: None)
        
        # Create service
        service = ProfileService(mock_session)
        
        # Test profile removal and expect DBError
        with pytest.raises(DBError) as exc_info:
            service.remove_profile(profile_id="profile123", user_id="user123")
        
        assert "Not found profile with id" in str(exc_info.value.msg)