import pytest
from app.api.v1.endpoints.chat import ChatRequest

pytestmark = pytest.mark.asyncio

@pytest.mark.asyncio
async def test_chat_missing_query():
    """Test chat request without query (should raise ValidationError)"""
    with pytest.raises(Exception):
        # query is required, so this should fail at model creation
        ChatRequest(max_results=5, include_sources=True)

@pytest.mark.asyncio
async def test_chat_invalid_max_results():
    """Test chat request with invalid max_results (should raise ValidationError)"""
    with pytest.raises(Exception):
        ChatRequest(query="test query", max_results=25, include_sources=True) 