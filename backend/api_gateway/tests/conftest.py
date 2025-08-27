"""pytest configuration and fixtures for API Gateway tests."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock
from sqlalchemy.orm import Session

# Import the main app
from app.main import app

# Import services for mocking
from app.services.users import UserService
from app.services.profiles import ProfileService

# Import clients for mocking
from app.clients.ai_quick_analysis import ai_quick_analysis_client
from app.clients.ai_quick_advisor import ai_quick_advisor_client
from app.clients.ai_rules import ai_rules_client


@pytest.fixture
def client():
    """Test client for making requests to the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def mock_user_service():
    """Mock UserService for testing."""
    return Mock(spec=UserService)


@pytest.fixture
def mock_profile_service():
    """Mock ProfileService for testing."""
    return Mock(spec=ProfileService)


@pytest.fixture
def mock_ai_clients():
    """Mock AI clients for testing."""
    # Store original clients
    original_analysis_client = ai_quick_analysis_client
    original_advisor_client = ai_quick_advisor_client
    original_rules_client = ai_rules_client
    
    # Replace with mocks
    mock_analysis_client = AsyncMock()
    mock_advisor_client = AsyncMock()
    mock_rules_client = AsyncMock()
    
    # Patch the modules
    import app.clients.ai_quick_analysis as analysis_module
    import app.clients.ai_quick_advisor as advisor_module
    import app.clients.ai_rules as rules_module
    
    analysis_module.ai_quick_analysis_client = mock_analysis_client
    advisor_module.ai_quick_advisor_client = mock_advisor_client
    rules_module.ai_rules_client = mock_rules_client
    
    yield {
        'analysis': mock_analysis_client,
        'advisor': mock_advisor_client,
        'rules': mock_rules_client
    }
    
    # Restore original clients
    analysis_module.ai_quick_analysis_client = original_analysis_client
    advisor_module.ai_quick_advisor_client = original_advisor_client
    rules_module.ai_rules_client = original_rules_client