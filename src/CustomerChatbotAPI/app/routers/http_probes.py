"""Health and readiness probes for Azure Container Apps."""

import logging

from fastapi import APIRouter, Request

from app.domain.models import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/health", response_model=HealthResponse, tags=["probes"])
async def health() -> HealthResponse:
    """Liveness probe — returns OK if the process is running."""
    return HealthResponse(status="healthy", version="0.1.0")


@router.get("/api/ready", response_model=HealthResponse, tags=["probes"])
async def ready(request: Request) -> HealthResponse:
    """Readiness probe — returns OK when dependencies are connected."""
    try:
        session_repo = getattr(request.app.state, "session_repository", None)
        if session_repo is not None:
            await session_repo.find_async({"id": "__health_check__"})
    except Exception:
        logger.warning("Readiness probe: Cosmos DB connectivity check failed")
        return HealthResponse(status="degraded", version="0.1.0")

    return HealthResponse(status="ready", version="0.1.0")
