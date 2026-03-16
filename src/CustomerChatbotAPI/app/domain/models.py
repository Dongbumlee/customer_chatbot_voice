"""API request/response models (Pydantic)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    """Request body for sending a chat message."""

    session_id: str = Field(..., pattern=r"^[a-f0-9\-]{36}$")
    content: str = Field(..., min_length=1, max_length=4000)
    modality: Literal["text", "voice"] = "text"


class ChatMessageResponse(BaseModel):
    """Response body for a chat message."""

    message_id: str
    session_id: str
    content: str
    agent: str | None = None
    metadata: dict | None = None
    timestamp: datetime


class AgentResponse(BaseModel):
    """Structured response from the agent orchestrator."""

    content: str
    agent: str
    intent: str
    product_cards: list[dict] | None = None
    metadata: dict | None = None


class ChatSessionResponse(BaseModel):
    """Response body for a chat session."""

    session_id: str
    title: str
    modality: str
    created_at: datetime
    last_active_at: datetime
    is_active: bool


class ProductResponse(BaseModel):
    """Response body for a product."""

    id: str
    name: str
    category: str
    price: float
    description: str
    image_url: str | None = None
    attributes: dict = {}


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
