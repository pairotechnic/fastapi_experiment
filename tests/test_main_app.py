import pytest

# Why not use aiohttp instead of httpx?
# aiohttp is a client library for making async requests to  external services
# httpx is built for testing ASGI apps. Its AsyncClient understands the ASGI Protocol
# talks directly to your FastAPI app in-process via ASGITransport, without a network
from httpx import AsyncClient, ASGITransport

# AsyncMock creates a fake async object - one you can await, and control the return value of
# patch temporarily replaces a real object with a fake object during a test, then restores it afterward
from unittest.mock import AsyncMock, patch

from main_app import app

# LifespanManager  is used to create app.state.session, prior to it being used
from asgi_lifespan import LifespanManager

# ------------------------------
# Fixtures
# ------------------------------

@pytest.fixture
async def client():
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client :
            yield client

class TestHealth:
    """Tests for /health endpoint"""

    # Decorator redundant because of asyncio_mode = auto in pytest.ini
    @pytest.mark.asyncio 
    async def test_health(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

class TestChat:
    """Tests for /chat endpoint"""

    # Decorator redundant because of asyncio_mode = auto in pytest.ini
    @pytest.mark.asyncio
    async def test_chat_success(self, client):
        mock_response_data = {
            "id": "mock-id-123",
            "content": "Success - Mock LLM Response",
            "model": "claude-opus-4-6",
            "provider": "Anthropic"
        }

        # We mock the aiohttp session so tests don't need the mock-llm container running
        mock_post = AsyncMock()
        mock_post.__aenter__ = AsyncMock(return_value=mock_post)
        mock_post.__aexit__ = AsyncMock(return_value=False)
        mock_post.status = 200 # Mock LLM response status
        mock_post.json = AsyncMock(return_value=mock_response_data)

        with patch.object(app.state.session, "post", return_value=mock_post):
            response = await client.post("/chat", json={
                "message": "hello",
                "model": "claude-opus-4-6",
                "provider": "Anthropic"
            })

        # Response status_code returned by /chat endpoint when it receives a 200 status from LLM
        assert response.status_code == 200 
        data = response.json()
        assert data["content"] == "Success - Mock LLM Response"
        assert data["provider"] == "Anthropic"

    # Decorator redundant because of asyncio_mode = auto in pytest.ini
    @pytest.mark.asyncio
    async def test_chat_llm_error(self, client):
        mock_post = AsyncMock()
        mock_post.__aenter__ = AsyncMock(return_value=mock_post)
        mock_post.__aexit__ = AsyncMock(return_value=False)
        mock_post.status = 403 # Simulate upstream error

        with patch.object(app.state.session, "post", return_value=mock_post):
            response = await client.post("/chat", json={
                "message": "hello",
                "provider": "OpenAI"
            })

        assert response.status_code == 502