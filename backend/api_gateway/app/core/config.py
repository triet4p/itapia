# app/core/config.py
"""
Centralized module for managing and accessing configuration variables.

Automatically reads values from the `.env` file in the project root directory.
Provides defined constants for other components in the application to use,
ensuring consistency and easy configuration changes from a single location.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# API Configuration
GATEWAY_V1_BASE_ROUTE = os.getenv("GATEWAY_V1_BASE_ROUTE", "/api/v1")
GATEWAY_ALLOW_ORIGINS = os.getenv('GATEWAY_ALLOW_ORIGINS', "").split(",")

# Client Configuration
AI_SERVICE_QUICK_HOST = os.getenv("AI_QUICK_HOST", 'localhost')
AI_SERVICE_QUICK_PORT = os.getenv("AI_QUICK_PORT", 8000)
AI_SERVICE_QUICK_V1_BASE_ROUTE = os.getenv("AI_QUICK_V1_BASE_ROUTE", "/api/v1")
AI_SERVICE_QUICK_BASE_URL = f'http://{AI_SERVICE_QUICK_HOST}:{AI_SERVICE_QUICK_PORT}{AI_SERVICE_QUICK_V1_BASE_ROUTE}'

# Google OAuth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Google OAuth URLs
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"

# Google OAuth Scopes
GOOGLE_OAUTH_SCOPES = ["https://www.googleapis.com/auth/userinfo.email",
                       "https://www.googleapis.com/auth/userinfo.profile",
                       "openid"]

# JWT Settings
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Redirect URIs
BACKEND_CALLBACK_URL = os.getenv('BACKEND_CALLBACK_URL')
FRONTEND_CALLBACK_URL = os.getenv('FRONTEND_CALLBACK_URL')
FRONTEND_LOGIN_ERR_URL = os.getenv('FRONTEND_LOGIN_ERR_URL')