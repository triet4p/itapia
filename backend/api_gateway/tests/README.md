# ITAPIA API Gateway Tests

This directory contains unit tests for the ITAPIA API Gateway.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                 # pytest configuration and fixtures
├── test_main.py                # Tests for the main application
├── test_core/                  # Tests for core modules
│   ├── __init__.py
│   ├── test_config.py          # Configuration tests
│   └── test_exceptions.py      # Custom exception tests
├── test_services/              # Tests for service modules
│   ├── __init__.py
│   ├── test_auth_service.py    # Authentication service tests
│   ├── test_user_service.py    # User service tests
│   └── test_profile_service.py # Profile service tests
├── test_api/                   # Tests for API endpoints
│   ├── __init__.py
│   ├── test_root.py            # Root endpoint tests
│   ├── test_auth.py            # Authentication endpoint tests
│   ├── test_users.py           # User endpoint tests
│   └── test_profiles.py        # Profile endpoint tests
├── test_clients/               # Tests for client modules
│   ├── __init__.py
│   ├── test_ai_quick_analysis.py  # AI quick analysis client tests
│   ├── test_ai_quick_advisor.py   # AI quick advisor client tests
│   └── test_ai_rules.py           # AI rules client tests
├── test_crud/                  # Tests for CRUD modules
│   ├── __init__.py
│   ├── test_users.py           # User CRUD tests
│   └── test_profiles.py        # Profile CRUD tests
├── requirements-test.txt       # Test dependencies
└── README.md                   # This file
```

## Running Tests

To run all tests:

```bash
cd backend/api_gateway
pytest
```

To run tests with coverage:

```bash
pytest --cov=app --cov-report=html
```

To run a specific test file:

```bash
pytest tests/test_main.py
```

To run tests in a specific directory:

```bash
pytest tests/test_services/
```

## Test Categories

### Unit Tests
- Test individual functions and methods
- Mock external dependencies
- Focus on logic and error handling

### Integration Tests
- Test interactions between components
- Test API endpoints
- Test database operations (using test database)

### End-to-End Tests
- Test complete user flows
- Test API Gateway with real services (in CI/CD)

## Test Dependencies

Install test dependencies:

```bash
pip install -r tests/requirements-test.txt
```

## Writing New Tests

1. Follow the existing structure and naming conventions
2. Use pytest fixtures for setup and teardown
3. Mock external dependencies
4. Test both success and error cases
5. Use descriptive test function names
6. Include docstrings for test functions