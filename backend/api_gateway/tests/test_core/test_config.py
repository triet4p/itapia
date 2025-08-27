"""Tests for the configuration module."""

import os
from app.core.config import (
    GATEWAY_V1_BASE_ROUTE,
    GATEWAY_ALLOW_ORIGINS,
    AI_SERVICE_QUICK_HOST,
    AI_SERVICE_QUICK_PORT,
    AI_SERVICE_QUICK_V1_BASE_ROUTE,
    AI_SERVICE_QUICK_BASE_URL,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    BACKEND_CALLBACK_URL,
    FRONTEND_CALLBACK_URL,
    FRONTEND_LOGIN_ERR_URL,
    GOOGLE_TOKEN_URL,
    GOOGLE_USERINFO_URL,
    GOOGLE_AUTH_URL,
    GOOGLE_OAUTH_SCOPES
)


def test_config_values():
    """Test that configuration values are loaded correctly."""
    # Test API configuration
    assert isinstance(GATEWAY_V1_BASE_ROUTE, str)
    assert GATEWAY_V1_BASE_ROUTE == "/api/v1" or GATEWAY_V1_BASE_ROUTE.startswith("/")
    
    # Test client configuration
    assert isinstance(AI_SERVICE_QUICK_HOST, str)
    assert isinstance(AI_SERVICE_QUICK_PORT, str) or isinstance(AI_SERVICE_QUICK_PORT, int)
    assert isinstance(AI_SERVICE_QUICK_V1_BASE_ROUTE, str)
    assert isinstance(AI_SERVICE_QUICK_BASE_URL, str)
    
    # Test that URLs are properly formatted
    assert AI_SERVICE_QUICK_BASE_URL.startswith("http")
    
    # Test OAuth configuration
    assert isinstance(GOOGLE_TOKEN_URL, str)
    assert GOOGLE_TOKEN_URL == "https://oauth2.googleapis.com/token"
    assert isinstance(GOOGLE_USERINFO_URL, str)
    assert GOOGLE_USERINFO_URL == "https://www.googleapis.com/oauth2/v3/userinfo"
    assert isinstance(GOOGLE_AUTH_URL, str)
    assert GOOGLE_AUTH_URL == "https://accounts.google.com/o/oauth2/v2/auth"
    
    # Test OAuth scopes
    assert isinstance(GOOGLE_OAUTH_SCOPES, list)
    assert len(GOOGLE_OAUTH_SCOPES) > 0
    for scope in GOOGLE_OAUTH_SCOPES:
        assert isinstance(scope, str)
        assert scope.startswith("https://")
    
    # Test JWT configuration
    assert isinstance(JWT_ALGORITHM, str)
    assert JWT_ALGORITHM == "HS256"
    assert isinstance(ACCESS_TOKEN_EXPIRE_MINUTES, int)
    assert ACCESS_TOKEN_EXPIRE_MINUTES > 0


def test_optional_config_values():
    """Test that optional configuration values have appropriate defaults."""
    # These might be None if not set in environment, but should be strings if set
    if GOOGLE_CLIENT_ID is not None:
        assert isinstance(GOOGLE_CLIENT_ID, str)
    if GOOGLE_CLIENT_SECRET is not None:
        assert isinstance(GOOGLE_CLIENT_SECRET, str)
    if JWT_SECRET_KEY is not None:
        assert isinstance(JWT_SECRET_KEY, str)
    if BACKEND_CALLBACK_URL is not None:
        assert isinstance(BACKEND_CALLBACK_URL, str)
    if FRONTEND_CALLBACK_URL is not None:
        assert isinstance(FRONTEND_CALLBACK_URL, str)
    if FRONTEND_LOGIN_ERR_URL is not None:
        assert isinstance(FRONTEND_LOGIN_ERR_URL, str)