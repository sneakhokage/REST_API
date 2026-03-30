import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from middleware.rate_limiter import rate_limit


def make_mock_request(host="127.0.0.1"):
    request = MagicMock()
    request.client.host = host
    return request


def make_mock_redis(request_count: int):
    mock_redis = AsyncMock()
    mock_redis.zremrangebyscore = AsyncMock()
    mock_redis.zcard = AsyncMock(return_value=request_count)
    mock_redis.zadd = AsyncMock()
    mock_redis.expire = AsyncMock()
    return mock_redis


@pytest.mark.asyncio
async def test_authenticated_under_limit():
    mock_redis = make_mock_redis(request_count=5)
    with patch("middleware.rate_limiter.get_redis", new=AsyncMock(return_value=mock_redis)):
        request = make_mock_request()
        await rate_limit(request, user_id="testuser")


@pytest.mark.asyncio
async def test_authenticated_over_limit():
    mock_redis = make_mock_redis(request_count=10)
    with patch("middleware.rate_limiter.get_redis", new=AsyncMock(return_value=mock_redis)):
        request = make_mock_request()
        with pytest.raises(HTTPException) as exc_info:
            await rate_limit(request, user_id="testuser")
        assert exc_info.value.status_code == 429


@pytest.mark.asyncio
async def test_anonymous_under_limit():
    mock_redis = make_mock_redis(request_count=1)
    with patch("middleware.rate_limiter.get_redis", new=AsyncMock(return_value=mock_redis)):
        request = make_mock_request(host="192.168.1.1")
        await rate_limit(request, user_id=None)


@pytest.mark.asyncio
async def test_anonymous_over_limit():
    mock_redis = make_mock_redis(request_count=2)
    with patch("middleware.rate_limiter.get_redis", new=AsyncMock(return_value=mock_redis)):
        request = make_mock_request(host="192.168.1.1")
        with pytest.raises(HTTPException) as exc_info:
            await rate_limit(request, user_id=None)
        assert exc_info.value.status_code == 429