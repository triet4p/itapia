"""Tests for the AI quick advisor client."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from app.clients.ai_quick_advisor import (
    get_full_quick_advisor,
    get_full_quick_advisor_explain,
)
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_get_full_quick_advisor_success():
    """Test successful full quick advisor retrieval."""
    # Mock response data
    mock_response_data = {
        "ticker": "AAPL",
        "advice": "BUY",
        "confidence": 0.90,
        "explanation": "Strong fundamentals and positive technical indicators",
    }

    # Create async mock response
    mock_response = AsyncMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None

    # Mock the client
    with patch("app.clients.ai_quick_advisor.ai_quick_advisor_client") as mock_client:
        mock_client.get.return_value = mock_response

        # Test the function
        result = await get_full_quick_advisor("AAPL", "user123")

        # Assertions
        assert result.ticker == "AAPL"
        assert result.advice == "BUY"
        assert result.confidence == 0.90
        mock_client.get.assert_called_once_with(
            "/advisor/AAPL/full", params={"user_id": "user123"}
        )


@pytest.mark.asyncio
async def test_get_full_quick_advisor_http_error():
    """Test full quick advisor retrieval when HTTP error occurs."""
    # Create async mock response with HTTP error
    mock_response = AsyncMock()
    mock_response.json.return_value = {"detail": "Advisor not available"}

    # Mock HTTPStatusError
    mock_error = httpx.HTTPStatusError(
        "Not Found", request=Mock(), response=mock_response
    )

    # Mock the client
    with patch("app.clients.ai_quick_advisor.ai_quick_advisor_client") as mock_client:
        mock_client.get.side_effect = mock_error

        # Test the function and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_full_quick_advisor("AAPL", "user123")

        assert exc_info.value.status_code == 404
        assert "Advisor not available" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_full_quick_advisor_request_error():
    """Test full quick advisor retrieval when request error occurs."""
    # Mock RequestError
    mock_error = httpx.RequestError("Connection failed")

    # Mock the client
    with patch("app.clients.ai_quick_advisor.ai_quick_advisor_client") as mock_client:
        mock_client.get.side_effect = mock_error

        # Test the function and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_full_quick_advisor("AAPL", "user123")

        assert exc_info.value.status_code == 503
        assert "AI Service is unavailable" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_full_quick_advisor_explain_success():
    """Test successful full quick advisor explanation retrieval."""
    # Mock response data (plain text)
    mock_response_text = "This is an explanation of the advice for AAPL"

    # Create async mock response
    mock_response = AsyncMock()
    mock_response.text = mock_response_text
    mock_response.raise_for_status.return_value = None

    # Mock the client
    with patch("app.clients.ai_quick_advisor.ai_quick_advisor_client") as mock_client:
        mock_client.get.return_value = mock_response

        # Test the function
        result = await get_full_quick_advisor_explain("AAPL", "user123")

        # Assertions
        assert result == mock_response_text
        mock_client.get.assert_called_once_with(
            "/advisor/AAPL/explain", params={"user_id": "user123"}
        )
