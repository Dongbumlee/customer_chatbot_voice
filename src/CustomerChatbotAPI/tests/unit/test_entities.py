"""Unit tests for domain entities."""

from datetime import datetime

import pytest

from app.domain.entities import ChatMessage, ChatSession, Product, UserProfile


class TestChatSession:
    """Tests for ChatSession entity creation and validation."""

    def test_create_chat_session_with_defaults(self) -> None:
        """ChatSession should initialise with sensible defaults."""
        # Arrange & Act
        session = ChatSession(
            id="session-001",
            user_id="user-001",
            title="My Chat",
        )

        # Assert
        assert session.id == "session-001"
        assert session.user_id == "user-001"
        assert session.title == "My Chat"
        assert session.modality == "text"
        assert session.is_active is True
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.last_active_at, datetime)

    def test_create_chat_session_voice_modality(self) -> None:
        """ChatSession should accept voice modality."""
        # Arrange & Act
        session = ChatSession(
            id="session-002",
            user_id="user-001",
            title="Voice Chat",
            modality="voice",
        )

        # Assert
        assert session.modality == "voice"

    def test_create_chat_session_mixed_modality(self) -> None:
        """ChatSession should accept mixed modality."""
        # Arrange & Act
        session = ChatSession(
            id="session-003",
            user_id="user-001",
            title="Mixed Chat",
            modality="mixed",
        )

        # Assert
        assert session.modality == "mixed"


class TestChatMessage:
    """Tests for ChatMessage entity creation and validation."""

    def test_create_user_message(self) -> None:
        """ChatMessage should store user messages correctly."""
        # Arrange & Act
        msg = ChatMessage(
            id="msg-001",
            session_id="session-001",
            role="user",
            content="Hello!",
            modality="text",
        )

        # Assert
        assert msg.id == "msg-001"
        assert msg.session_id == "session-001"
        assert msg.role == "user"
        assert msg.content == "Hello!"
        assert msg.modality == "text"
        assert msg.agent is None
        assert msg.metadata is None

    def test_create_assistant_message_with_agent(self) -> None:
        """ChatMessage should store agent attribution."""
        # Arrange & Act
        msg = ChatMessage(
            id="msg-002",
            session_id="session-001",
            role="assistant",
            content="Product found!",
            modality="text",
            agent="product",
            metadata={"product_cards": [{"id": "p1"}]},
        )

        # Assert
        assert msg.agent == "product"
        assert msg.metadata == {"product_cards": [{"id": "p1"}]}

    def test_create_voice_message(self) -> None:
        """ChatMessage should support voice modality."""
        # Arrange & Act
        msg = ChatMessage(
            id="msg-003",
            session_id="session-001",
            role="user",
            content="spoken text",
            modality="voice",
        )

        # Assert
        assert msg.modality == "voice"


class TestProduct:
    """Tests for Product entity creation and validation."""

    def test_create_product_with_required_fields(self) -> None:
        """Product should be created with required fields."""
        # Arrange & Act
        product = Product(
            id="prod-001",
            name="Headphones",
            category="electronics",
            price=49.99,
            description="Wireless headphones",
        )

        # Assert
        assert product.id == "prod-001"
        assert product.name == "Headphones"
        assert product.category == "electronics"
        assert product.price == 49.99
        assert product.is_active is True
        assert product.image_url is None
        assert product.attributes == {}

    def test_create_product_with_all_fields(self) -> None:
        """Product should accept optional fields."""
        # Arrange & Act
        product = Product(
            id="prod-002",
            name="Laptop",
            category="computers",
            price=999.99,
            description="16 inch laptop",
            image_url="https://example.com/laptop.jpg",
            attributes={"ram": "16GB", "storage": "512GB"},
            is_active=False,
        )

        # Assert
        assert product.image_url == "https://example.com/laptop.jpg"
        assert product.attributes == {"ram": "16GB", "storage": "512GB"}
        assert product.is_active is False


class TestUserProfile:
    """Tests for UserProfile entity creation and validation."""

    def test_create_user_profile(self) -> None:
        """UserProfile should store Entra ID user data."""
        # Arrange & Act
        profile = UserProfile(
            id="user-001",
            display_name="Jane Doe",
            email="jane@example.com",
            entra_oid="00000000-0000-0000-0000-000000000001",
        )

        # Assert
        assert profile.id == "user-001"
        assert profile.display_name == "Jane Doe"
        assert profile.email == "jane@example.com"
        assert profile.entra_oid == "00000000-0000-0000-0000-000000000001"
        assert profile.preferences == {}
        assert profile.last_login is None
