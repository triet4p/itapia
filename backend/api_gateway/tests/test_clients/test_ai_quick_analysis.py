"""Tests for the AI quick analysis client."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from app.clients.ai_quick_analysis import (
    get_forecasting_quick_analysis,
    get_full_quick_analysis,
    get_full_quick_analysis_explain,
    get_news_quick_analysis,
    get_technical_quick_analysis,
)
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_get_full_quick_analysis_success():
    """Test successful full quick analysis retrieval."""
    # Mock response data
    mock_response_data = {
        "ticker": "AAPL",
        "overall_signal": "BUY",
        "confidence": 0.85,
        "technical_analysis": {},
        "news_sentiment": {},
        "forecast": {},
    }

    # Create async mock response
    mock_response = AsyncMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None

    # Mock the client
    with patch("app.clients.ai_quick_analysis.ai_quick_analysis_client") as mock_client:
        mock_client.get.return_value = mock_response

        # Test the function
        result = await get_full_quick_analysis("AAPL")

        # Assertions
        assert result.ticker == "AAPL"
        assert result.overall_signal == "BUY"
        assert result.confidence == 0.85
        mock_client.get.assert_called_once_with(
            "/analysis/AAPL/full",
            params={"daily_analysis_type": "medium", "required_type": "all"},
        )


@pytest.mark.asyncio
async def test_get_full_quick_analysis_http_error():
    """Test full quick analysis retrieval when HTTP error occurs."""
    # Create async mock response with HTTP error
    mock_response = AsyncMock()
    mock_response.json.return_value = {"detail": "Analysis not available"}

    # Mock HTTPStatusError
    mock_error = httpx.HTTPStatusError(
        "Not Found", request=Mock(), response=mock_response
    )

    # Mock the client
    with patch("app.clients.ai_quick_analysis.ai_quick_analysis_client") as mock_client:
        mock_client.get.side_effect = mock_error

        # Test the function and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_full_quick_analysis("AAPL")

        assert exc_info.value.status_code == 404
        assert "Analysis not available" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_full_quick_analysis_request_error():
    """Test full quick analysis retrieval when request error occurs."""
    # Mock RequestError
    mock_error = httpx.RequestError("Connection failed")

    # Mock the client
    with patch("app.clients.ai_quick_analysis.ai_quick_analysis_client") as mock_client:
        mock_client.get.side_effect = mock_error

        # Test the function and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_full_quick_analysis("AAPL")

        assert exc_info.value.status_code == 503
        assert "AI Service is unavailable" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_technical_quick_analysis_success():
    """Test successful technical quick analysis retrieval."""
    # Mock response data
    mock_response_data = {
        "ticker": "AAPL",
        "technical_signals": [],
        "overall_technical_signal": "BUY",
        "confidence": 0.75,
    }

    # Create async mock response
    mock_response = AsyncMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None

    # Mock the client
    with patch("app.clients.ai_quick_analysis.ai_quick_analysis_client") as mock_client:
        mock_client.get.return_value = mock_response

        # Test the function
        result = await get_technical_quick_analysis("AAPL")

        # Assertions
        assert result.ticker == "AAPL"
        assert result.overall_technical_signal == "BUY"
        assert result.confidence == 0.75
        mock_client.get.assert_called_once_with(
            "/analysis/AAPL/technical",
            params={"daily_analysis_type": "medium", "required_type": "all"},
        )


@pytest.mark.asyncio
async def test_get_forecasting_quick_analysis_success():
    """Test successful forecasting quick analysis retrieval."""
    # Mock response data
    mock_response_data = {
        "ticker": "AAPL",
        "forecast_signals": [],
        "overall_forecast_signal": "BUY",
        "confidence": 0.80,
    }

    # Create async mock response
    mock_response = AsyncMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None

    # Mock the client
    with patch("app.clients.ai_quick_analysis.ai_quick_analysis_client") as mock_client:
        mock_client.get.return_value = mock_response

        # Test the function
        result = await get_forecasting_quick_analysis("AAPL")

        # Assertions
        assert result.ticker == "AAPL"
        assert result.overall_forecast_signal == "BUY"
        assert result.confidence == 0.80
        mock_client.get.assert_called_once_with("/analysis/AAPL/forecasting")


@pytest.mark.asyncio
async def test_get_news_quick_analysis_success():
    """Test successful news quick analysis retrieval."""
    # Mock response data
    mock_response_data = {
        "ticker": "AAPL",
        "news_signals": [],
        "overall_news_signal": "NEUTRAL",
        "confidence": 0.65,
    }

    # Create async mock response
    mock_response = AsyncMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None

    # Mock the client
    with patch("app.clients.ai_quick_analysis.ai_quick_analysis_client") as mock_client:
        mock_client.get.return_value = mock_response

        # Test the function
        result = await get_news_quick_analysis("AAPL")

        # Assertions
        assert result.ticker == "AAPL"
        assert result.overall_news_signal == "NEUTRAL"
        assert result.confidence == 0.65
        mock_client.get.assert_called_once_with("/analysis/AAPL/news")


@pytest.mark.asyncio
async def test_get_full_quick_analysis_explain_success():
    """Test successful full quick analysis explanation retrieval."""
    # Mock response data (plain text)
    mock_response_text = "This is an explanation of the analysis for AAPL"

    # Create async mock response
    mock_response = AsyncMock()
    mock_response.text = mock_response_text
    mock_response.raise_for_status.return_value = None

    # Mock the client
    with patch("app.clients.ai_quick_analysis.ai_quick_analysis_client") as mock_client:
        mock_client.get.return_value = mock_response

        # Test the function
        result = await get_full_quick_analysis_explain("AAPL")

        # Assertions
        assert result == mock_response_text
        mock_client.get.assert_called_once_with(
            "/analysis/AAPL/explain",
            params={
                "daily_analysis_type": "medium",
                "required_type": "all",
                "explain_type": "all",
            },
        )
