"""Unit test fixtures and shared helpers."""

import pytest

from app.domain.entities import ChatMessage, ChatSession, Product, UserProfile


@pytest.fixture
def sample_chat_session() -> ChatSession:
    """Create a sample ChatSession entity for testing."""
    return ChatSession(
        id="session-001",
        user_id="user-001",
        title="Test Session",
        modality="text",
    )


@pytest.fixture
def sample_chat_message() -> ChatMessage:
    """Create a sample ChatMessage entity for testing."""
    return ChatMessage(
        id="msg-001",
        session_id="session-001",
        role="user",
        content="Hello, can you help me find a product?",
        modality="text",
    )


@pytest.fixture
def sample_product() -> Product:
    """Create a sample Product entity for testing."""
    return Product(
        id="prod-001",
        name="Wireless Headphones",
        category="electronics",
        price=79.99,
        description="High-quality wireless headphones with noise cancellation",
        image_url="https://example.com/images/headphones.jpg",
    )


@pytest.fixture
def sample_user_profile() -> UserProfile:
    """Create a sample UserProfile entity for testing."""
    return UserProfile(
        id="user-001",
        display_name="Test User",
        email="test@example.com",
        entra_oid="00000000-0000-0000-0000-000000000001",
    )
