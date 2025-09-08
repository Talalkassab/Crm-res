import pytest
import time
from unittest.mock import patch, MagicMock
from src.middleware.rate_limiter import RateLimiter

@pytest.fixture
def mock_redis():
    with patch('src.middleware.rate_limiter.redis.from_url') as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client

def test_rate_limiter_initialization(mock_redis):
    limiter = RateLimiter(
        redis_url="redis://localhost:6379",
        business_rate_limit=80,
        user_rate_limit=1000,
        window_seconds=1
    )
    
    assert limiter.business_rate_limit == 80
    assert limiter.user_rate_limit == 1000
    assert limiter.window_seconds == 1

@pytest.mark.asyncio
async def test_check_rate_limit_under_limit(mock_redis):
    limiter = RateLimiter()
    
    mock_pipeline = MagicMock()
    mock_pipeline.execute.return_value = [50, True]
    mock_redis.pipeline.return_value = mock_pipeline
    
    allowed, count = await limiter.check_rate_limit("test_user", is_user_initiated=False)
    
    assert allowed is True
    assert count == 50

@pytest.mark.asyncio
async def test_check_rate_limit_over_limit(mock_redis):
    limiter = RateLimiter()
    
    mock_pipeline = MagicMock()
    mock_pipeline.execute.return_value = [85, True]
    mock_redis.pipeline.return_value = mock_pipeline
    
    allowed, count = await limiter.check_rate_limit("test_user", is_user_initiated=False)
    
    assert allowed is False
    assert count == 85

@pytest.mark.asyncio
async def test_user_initiated_rate_limit(mock_redis):
    limiter = RateLimiter()
    
    mock_pipeline = MagicMock()
    mock_pipeline.execute.return_value = [500, True]
    mock_redis.pipeline.return_value = mock_pipeline
    
    allowed, count = await limiter.check_rate_limit("test_user", is_user_initiated=True)
    
    assert allowed is True
    assert count == 500

@pytest.mark.asyncio
async def test_user_initiated_rate_limit_exceeded(mock_redis):
    limiter = RateLimiter()
    
    mock_pipeline = MagicMock()
    mock_pipeline.execute.return_value = [1001, True]
    mock_redis.pipeline.return_value = mock_pipeline
    
    allowed, count = await limiter.check_rate_limit("test_user", is_user_initiated=True)
    
    assert allowed is False
    assert count == 1001

def test_get_usage_stats(mock_redis):
    limiter = RateLimiter()
    
    mock_redis.get.side_effect = [b'30', b'500']
    
    stats = limiter.get_usage_stats("test_user")
    
    assert stats["business"]["current"] == 30
    assert stats["business"]["limit"] == 80
    assert stats["business"]["remaining"] == 50
    assert stats["user"]["current"] == 500
    assert stats["user"]["limit"] == 1000
    assert stats["user"]["remaining"] == 500

def test_get_usage_stats_no_data(mock_redis):
    limiter = RateLimiter()
    
    mock_redis.get.side_effect = [None, None]
    
    stats = limiter.get_usage_stats("test_user")
    
    assert stats["business"]["current"] == 0
    assert stats["business"]["remaining"] == 80
    assert stats["user"]["current"] == 0
    assert stats["user"]["remaining"] == 1000

@pytest.mark.asyncio
async def test_wait_if_needed_no_wait(mock_redis):
    limiter = RateLimiter()
    
    mock_pipeline = MagicMock()
    mock_pipeline.execute.return_value = [50, True]
    mock_redis.pipeline.return_value = mock_pipeline
    
    wait_time = await limiter.wait_if_needed("test_user", is_user_initiated=False)
    
    assert wait_time == 0

@pytest.mark.asyncio
async def test_wait_if_needed_with_wait(mock_redis):
    limiter = RateLimiter(window_seconds=0.1)
    
    mock_pipeline = MagicMock()
    mock_pipeline.execute.return_value = [85, True]
    mock_redis.pipeline.return_value = mock_pipeline
    
    start_time = time.time()
    wait_time = await limiter.wait_if_needed("test_user", is_user_initiated=False)
    elapsed = time.time() - start_time
    
    assert wait_time == 0.1
    assert elapsed >= 0.1

def test_get_key_format():
    limiter = RateLimiter()
    
    with patch('time.time', return_value=1234567890):
        key = limiter._get_key("test_user", "business")
        
        assert key.startswith("rate_limit:business:test_user:")
        assert "1234567890" in key