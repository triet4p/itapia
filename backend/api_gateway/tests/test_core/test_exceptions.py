"""Tests for custom exceptions."""

from app.core.exceptions import AuthError, DBError, NoDataError, ServerCredError


def test_auth_error():
    """Test AuthError exception."""
    error_msg = "Authentication failed"
    exc = AuthError(error_msg)
    assert exc.msg == error_msg
    assert str(exc) == ""  # AuthError doesn't call super().__init__() with message


def test_no_data_error():
    """Test NoDataError exception."""
    error_msg = "No data found"
    exc = NoDataError(error_msg)
    assert exc.msg == error_msg
    assert str(exc) == ""  # NoDataError doesn't call super().__init__() with message


def test_db_error():
    """Test DBError exception."""
    error_msg = "Database error"
    exc = DBError(error_msg)
    assert exc.msg == error_msg
    assert str(exc) == ""  # DBError doesn't call super().__init__() with message


def test_server_cred_error():
    """Test ServerCredError exception."""
    detail = "Invalid credentials"
    header = {"WWW-Authenticate": "Bearer"}
    exc = ServerCredError(detail, header)
    assert exc.detail == detail
    assert exc.header == header
    assert (
        str(exc) == ""
    )  # ServerCredError doesn't call super().__init__() with message
