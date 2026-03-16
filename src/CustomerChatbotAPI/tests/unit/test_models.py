"""Unit tests for API request/response models."""

from datetime import datetime, timezone

import pytest
from app.domain.models import (
    AgentResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionResponse,
    HealthResponse,
    ProductResponse,
)
from pydantic import ValidationError


class TestChatMessageRequest:
    """Tests for ChatMessageRequest validation."""

    def test_valid_text_request(self) -> None:
        # Arrange & Act
        req = ChatMessageRequest(
            session_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            content="Hello",
            modality="text",
        )

        # Assert
        assert req.session_id == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        assert req.content == "Hello"
        assert req.modality == "text"

    def test_default_modality_is_text(self) -> None:
        # Arrange & Act
        req = ChatMessageRequest(
            session_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890", content="Hello"
        )

        # Assert
        assert req.modality == "text"

    def test_voice_modality_accepted(self) -> None:
        # Arrange & Act
        req = ChatMessageRequest(
            session_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            content="Audio text",
            modality="voice",
        )

        # Assert
        assert req.modality == "voice"

    def test_missing_session_id_raises(self) -> None:
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            ChatMessageRequest(content="Hello")

    def test_missing_content_raises(self) -> None:
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            ChatMessageRequest(session_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890")

    def test_invalid_session_id_format_raises(self) -> None:
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            ChatMessageRequest(session_id="not-a-uuid", content="Hello")

    def test_content_too_long_raises(self) -> None:
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            ChatMessageRequest(
                session_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                content="x" * 4001,
            )

    def test_empty_content_raises(self) -> None:
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            ChatMessageRequest(
                session_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                content="",
            )


class TestChatMessageResponse:
    """Tests for ChatMessageResponse serialization."""

    def test_valid_response(self) -> None:
        # Arrange
        now = datetime.now(timezone.utc)

        # Act
        resp = ChatMessageResponse(
            message_id="m-001",
            session_id="s-001",
            content="Hi there!",
            agent="chat",
            timestamp=now,
        )

        # Assert
        assert resp.message_id == "m-001"
        assert resp.agent == "chat"
        assert resp.metadata is None

    def test_response_with_metadata(self) -> None:
        # Arrange & Act
        resp = ChatMessageResponse(
            message_id="m-002",
            session_id="s-001",
            content="Found products",
            agent="product",
            metadata={"product_cards": [{"id": "p1"}]},
            timestamp=datetime.now(timezone.utc),
        )

        # Assert
        assert resp.metadata == {"product_cards": [{"id": "p1"}]}


class TestAgentResponse:
    """Tests for AgentResponse model."""

    def test_basic_agent_response(self) -> None:
        # Arrange & Act
        resp = AgentResponse(
            content="Hello!",
            agent="chat",
            intent="general",
        )

        # Assert
        assert resp.content == "Hello!"
        assert resp.agent == "chat"
        assert resp.intent == "general"
        assert resp.product_cards is None
        assert resp.metadata is None

    def test_agent_response_with_product_cards(self) -> None:
        # Arrange & Act
        resp = AgentResponse(
            content="Check these out",
            agent="product",
            intent="product",
            product_cards=[{"id": "p1", "name": "Widget"}],
        )

        # Assert
        assert len(resp.product_cards) == 1
        assert resp.product_cards[0]["name"] == "Widget"


class TestProductResponse:
    """Tests for ProductResponse model."""

    def test_valid_product_response(self) -> None:
        # Arrange & Act
        resp = ProductResponse(
            id="prod-001",
            name="Headphones",
            category="electronics",
            price=79.99,
            description="Noise cancelling",
        )

        # Assert
        assert resp.id == "prod-001"
        assert resp.price == 79.99
        assert resp.image_url is None
        assert resp.attributes == {}


class TestHealthResponse:
    """Tests for HealthResponse model."""

    def test_healthy_response(self) -> None:
        # Arrange & Act
        resp = HealthResponse(status="healthy", version="0.1.0")

        # Assert
        assert resp.status == "healthy"
        assert resp.version == "0.1.0"

    def test_degraded_response(self) -> None:
        # Arrange & Act
        resp = HealthResponse(status="degraded", version="0.1.0")

        # Assert
        assert resp.status == "degraded"


class TestChatSessionResponse:
    """Tests for ChatSessionResponse model."""

    def test_valid_session_response(self) -> None:
        # Arrange
        now = datetime.now(timezone.utc)

        # Act
        resp = ChatSessionResponse(
            session_id="s-001",
            title="My Chat",
            modality="text",
            created_at=now,
            last_active_at=now,
            is_active=True,
        )

        # Assert
        assert resp.session_id == "s-001"
        assert resp.is_active is True
