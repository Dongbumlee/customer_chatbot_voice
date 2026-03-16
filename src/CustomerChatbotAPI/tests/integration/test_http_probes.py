"""Integration tests for HTTP health and readiness probes."""

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def api_client_no_lifespan() -> AsyncClient:
    """Create an HTTP client using a minimal app without Azure dependencies.

    The full `lifespan` requires live Azure credentials. For probe
    integration tests we create the app directly and optionally
    set mock state so that the readiness probe can exercise its logic.
    """
    from app.main import create_app

    app = create_app()

    # Simulate initialised state for readiness probe
    from unittest.mock import AsyncMock

    mock_session_repo = AsyncMock()
    mock_session_repo.find_async = AsyncMock(return_value=[])
    app.state.session_repository = mock_session_repo

    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


class TestHealthProbe:
    """Tests for the /api/health liveness probe."""

    async def test_health_returns_200(
        self, api_client_no_lifespan: AsyncClient
    ) -> None:
        """Liveness probe should return HTTP 200 with healthy status."""
        # Arrange
        client = api_client_no_lifespan

        # Act
        response = await client.get("/api/health")

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "healthy"
        assert body["version"] == "0.1.0"


class TestReadinessProbe:
    """Tests for the /api/ready readiness probe."""

    async def test_ready_returns_200_when_healthy(
        self,
        api_client_no_lifespan: AsyncClient,
    ) -> None:
        """Readiness probe should return HTTP 200 when Cosmos DB is reachable."""
        # Arrange
        client = api_client_no_lifespan

        # Act
        response = await client.get("/api/ready")

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ready"

    async def test_ready_returns_degraded_on_db_failure(self) -> None:
        """Readiness probe should return degraded when Cosmos DB fails."""
        # Arrange
        from unittest.mock import AsyncMock

        from app.main import create_app

        app = create_app()
        mock_session_repo = AsyncMock()
        mock_session_repo.find_async = AsyncMock(
            side_effect=Exception("Connection refused"),
        )
        app.state.session_repository = mock_session_repo

        transport = ASGITransport(app=app)
        client = AsyncClient(transport=transport, base_url="http://test")

        # Act
        response = await client.get("/api/ready")

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "degraded"
