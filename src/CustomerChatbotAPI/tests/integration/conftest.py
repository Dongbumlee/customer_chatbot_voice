"""Integration test fixtures — requires live Azure resources."""

import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def api_client() -> AsyncClient:
    """Create an async HTTP client for integration testing against the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
