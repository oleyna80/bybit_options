import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from bybit_options.services.telegram_alerter import TelegramAlerter

@pytest.fixture
def alerter():
    return TelegramAlerter(token="test_token", chat_id="test_chat")

@pytest.mark.asyncio
async def test_telegram_init(alerter):
    assert alerter.enabled is True
    assert alerter.token == "test_token"
    assert alerter.chat_id == "test_chat"

@pytest.mark.asyncio
async def test_telegram_disabled_by_default():
    with patch("os.getenv", return_value=None):
        a = TelegramAlerter()
        assert a.enabled is False

@pytest.mark.asyncio
async def test_send_message_rate_limit(alerter):
    # Mock Response Context Manager
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text.return_value = "ok"
    
    mock_post_ctx = AsyncMock()
    mock_post_ctx.__aenter__.return_value = mock_response
    
    # Mock Session
    mock_session = AsyncMock()
    # Important: post must be synchronous returning context manager
    mock_session.post = MagicMock(return_value=mock_post_ctx)
    mock_session.closed = False
    
    # Patch ClientSession
    with patch("aiohttp.ClientSession", return_value=mock_session):
        start_time = asyncio.get_running_loop().time()
        
        await alerter.send_message("msg1")
        await alerter.send_message("msg2")
        
        end_time = asyncio.get_running_loop().time()
        
        # Should take at least 1 second due to rate limit
        duration = end_time - start_time
        assert duration >= 0.9 
        
        assert mock_session.post.call_count == 2
