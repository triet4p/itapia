"""Tests for the AI rules client."""

import pytest
from unittest.mock import AsyncMock, patch
import httpx
from fastapi import HTTPException

from app.clients.ai_rules import (
    get_single_rule_explain,
    get_ready_rules,
    get_nodes
)
from itapia_common.schemas.api.rules import NodeType, SemanticType


@pytest.mark.asyncio
async def test_get_single_rule_explain_success():
    """Test successful single rule explanation retrieval."""
    # Mock response data
    mock_response_data = {
        "rule_id": "RULE_001",
        "explanation": "This rule evaluates technical indicators",
        "confidence": 0.85
    }
    
    # Create async mock response
    mock_response = AsyncMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    
    # Mock the client
    with patch('app.clients.ai_rules.ai_rules_client') as mock_client:
        mock_client.get.return_value = mock_response
        
        # Test the function
        result = await get_single_rule_explain("RULE_001")
        
        # Assertions
        assert result.rule_id == "RULE_001"
        assert result.explanation == "This rule evaluates technical indicators"
        assert result.confidence == 0.85
        mock_client.get.assert_called_once_with("/rules/RULE_001/explain", params={})


@pytest.mark.asyncio
async def test_get_active_rules_success():
    """Test successful active rules retrieval."""
    # Mock response data
    mock_response_data = [
        {
            "rule_id": "RULE_001",
            "name": "Technical Analysis Rule",
            "description": "Evaluates technical indicators",
            "purpose": "TECHNICAL"
        },
        {
            "rule_id": "RULE_002",
            "name": "News Sentiment Rule",
            "description": "Analyzes news sentiment",
            "purpose": "NEWS"
        }
    ]
    
    # Create async mock response
    mock_response = AsyncMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    
    # Mock the client
    with patch('app.clients.ai_rules.ai_rules_client') as mock_client:
        mock_client.get.return_value = mock_response
        
        # Test the function
        result = await get_ready_rules(SemanticType.ANY)
        
        # Assertions
        assert len(result) == 2
        assert result[0].rule_id == "RULE_001"
        assert result[1].rule_id == "RULE_002"
        mock_client.get.assert_called_once_with("/rules", params={
            "purpose": "ANY"
        })


@pytest.mark.asyncio
async def test_get_nodes_success():
    """Test successful nodes retrieval."""
    # Mock response data
    mock_response_data = [
        {
            "node_id": "NODE_001",
            "node_name": "RSI Indicator",
            "node_type": "TECHNICAL",
            "purpose": "TECHNICAL"
        },
        {
            "node_id": "NODE_002",
            "node_name": "News Sentiment",
            "node_type": "NEWS",
            "purpose": "NEWS"
        }
    ]
    
    # Create async mock response
    mock_response = AsyncMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    
    # Mock the client
    with patch('app.clients.ai_rules.ai_rules_client') as mock_client:
        mock_client.get.return_value = mock_response
        
        # Test the function
        result = await get_nodes(NodeType.ANY, SemanticType.ANY)
        
        # Assertions
        assert len(result) == 2
        assert result[0].node_id == "NODE_001"
        assert result[1].node_id == "NODE_002"
        mock_client.get.assert_called_once_with("/rules/nodes", params={
            "purpose": "ANY",
            "node_type": "ANY"
        })


@pytest.mark.asyncio
async def test_get_single_rule_explain_http_error():
    """Test single rule explanation retrieval when HTTP error occurs."""
    # Create async mock response with HTTP error
    mock_response = AsyncMock()
    mock_response.json.return_value = {"detail": "Rule not found"}
    
    # Mock HTTPStatusError
    mock_error = httpx.HTTPStatusError(
        "Not Found",
        request=Mock(),
        response=mock_response
    )
    
    # Mock the client
    with patch('app.clients.ai_rules.ai_rules_client') as mock_client:
        mock_client.get.side_effect = mock_error
        
        # Test the function and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_single_rule_explain("NONEXISTENT_RULE")
        
        assert exc_info.value.status_code == 404
        assert "Rule not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_active_rules_request_error():
    """Test active rules retrieval when request error occurs."""
    # Mock RequestError
    mock_error = httpx.RequestError("Connection failed")
    
    # Mock the client
    with patch('app.clients.ai_rules.ai_rules_client') as mock_client:
        mock_client.get.side_effect = mock_error
        
        # Test the function and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_ready_rules(SemanticType.ANY)
        
        assert exc_info.value.status_code == 503
        assert "AI Service is unavailable" in str(exc_info.value.detail)