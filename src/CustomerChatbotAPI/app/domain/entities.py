"""Cosmos DB entities using sas-cosmosdb Repository Pattern."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import Field
from sas.cosmosdb.sql import RootEntityBase


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ChatSession(RootEntityBase["ChatSession", str]):
    """Represents a user chat session."""

    user_id: str
    title: str
    modality: Literal["text", "voice", "mixed"] = "text"
    created_at: datetime = Field(default_factory=_utcnow)
    last_active_at: datetime = Field(default_factory=_utcnow)
    is_active: bool = True


class ChatMessage(RootEntityBase["ChatMessage", str]):
    """Represents a single conversation turn within a session."""

    session_id: str  # partition key
    role: Literal["user", "assistant", "system"]
    content: str
    modality: Literal["text", "voice"]
    agent: str | None = None  # which agent responded
    metadata: dict | None = None  # product cards, links, etc.
    timestamp: datetime = Field(default_factory=_utcnow)


class UserProfile(RootEntityBase["UserProfile", str]):
    """Represents a user profile linked to Microsoft Entra ID."""

    display_name: str
    email: str
    entra_oid: str  # Microsoft Entra Object ID
    preferences: dict = {}
    last_login: datetime | None = None


class Product(RootEntityBase["Product", str]):
    """Represents a product in the catalog."""

    name: str
    category: str
    price: float
    description: str
    image_url: str | None = None
    attributes: dict = {}
    is_active: bool = True
