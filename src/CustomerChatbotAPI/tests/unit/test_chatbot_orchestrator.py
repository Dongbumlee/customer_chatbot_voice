"""Unit tests for the ChatbotOrchestrator."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.domain.enums import Intent
from app.domain.models import AgentResponse
from app.services.chatbot_orchestrator import ChatbotOrchestrator


@pytest.fixture
def mock_openai_client() -> AsyncMock:
    """Create a mock AsyncAzureOpenAI client."""
    client = AsyncMock()
    return client


@pytest.fixture
def mock_chat_agent() -> AsyncMock:
    """Create a mock ChatAgent."""
    agent = AsyncMock()
    agent.process_async = AsyncMock(return_value="Hello! I'm here to help.")
    return agent


@pytest.fixture
def mock_product_agent() -> AsyncMock:
    """Create a mock ProductAgent."""
    agent = AsyncMock()
    agent.process_async = AsyncMock(
        return_value={
            "content": "Here are some headphones.",
            "product_cards": [
                {
                    "id": "p1",
                    "name": "Headphones",
                    "category": "electronics",
                    "price": 79.99,
                    "description": "Wireless",
                    "image_url": None,
                }
            ],
        }
    )
    return agent


@pytest.fixture
def mock_policy_agent() -> AsyncMock:
    """Create a mock PolicyAgent."""
    agent = AsyncMock()
    agent.process_async = AsyncMock(
        return_value={
            "content": "Our return policy allows 30-day returns.",
            "sources": [{"title": "Return Policy", "source": "returns-policy.md"}],
        }
    )
    return agent


@pytest.fixture
def mock_session_repo() -> AsyncMock:
    """Create a mock ChatSessionRepository."""
    repo = AsyncMock()
    repo.get_async = AsyncMock(return_value=MagicMock(last_active_at=None))
    repo.update_async = AsyncMock()
    return repo


@pytest.fixture
def mock_message_repo() -> AsyncMock:
    """Create a mock ChatMessageRepository."""
    repo = AsyncMock()
    repo.add_async = AsyncMock()
    repo.find_async = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def orchestrator(
    mock_openai_client: AsyncMock,
    mock_chat_agent: AsyncMock,
    mock_product_agent: AsyncMock,
    mock_policy_agent: AsyncMock,
    mock_session_repo: AsyncMock,
    mock_message_repo: AsyncMock,
) -> ChatbotOrchestrator:
    """Create a ChatbotOrchestrator with all mocked dependencies."""
    return ChatbotOrchestrator(
        openai_client=mock_openai_client,
        deployment_name="gpt-4o",
        chat_agent=mock_chat_agent,
        product_agent=mock_product_agent,
        policy_agent=mock_policy_agent,
        session_repository=mock_session_repo,
        message_repository=mock_message_repo,
    )


class TestClassifyIntent:
    """Tests for intent classification."""

    async def test_classify_product_intent(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_openai_client: AsyncMock,
    ) -> None:
        """Intent classifier should return PRODUCT for product queries."""
        # Arrange
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="product"))]
        mock_openai_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        # Act
        intent = await orchestrator.classify_intent_async("Show me headphones")

        # Assert
        assert intent == Intent.PRODUCT

    async def test_classify_policy_intent(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_openai_client: AsyncMock,
    ) -> None:
        """Intent classifier should return POLICY for policy queries."""
        # Arrange
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="policy"))]
        mock_openai_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        # Act
        intent = await orchestrator.classify_intent_async("What is your return policy?")

        # Assert
        assert intent == Intent.POLICY

    async def test_classify_general_intent(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_openai_client: AsyncMock,
    ) -> None:
        """Intent classifier should return GENERAL for greetings."""
        # Arrange
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="general"))]
        mock_openai_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        # Act
        intent = await orchestrator.classify_intent_async("Hello!")

        # Assert
        assert intent == Intent.GENERAL

    async def test_classify_unknown_defaults_to_general(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_openai_client: AsyncMock,
    ) -> None:
        """Unrecognised classification should default to GENERAL."""
        # Arrange
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="unknown"))]
        mock_openai_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        # Act
        intent = await orchestrator.classify_intent_async("asdfghjkl")

        # Assert
        assert intent == Intent.GENERAL


class TestProcessMessage:
    """Tests for end-to-end message processing."""

    async def test_routes_to_product_agent(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_openai_client: AsyncMock,
        mock_product_agent: AsyncMock,
        mock_message_repo: AsyncMock,
    ) -> None:
        """Product intent should route to ProductAgent."""
        # Arrange
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="product"))]
        mock_openai_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        # Act
        result = await orchestrator.process_message_async(
            session_id="s-001",
            user_message="Show me laptops",
            modality="text",
        )

        # Assert
        assert isinstance(result, AgentResponse)
        assert result.agent == "product"
        assert result.intent == "product"
        assert result.product_cards is not None
        mock_product_agent.process_async.assert_awaited_once()
        assert mock_message_repo.add_async.await_count == 2

    async def test_routes_to_policy_agent(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_openai_client: AsyncMock,
        mock_policy_agent: AsyncMock,
    ) -> None:
        """Policy intent should route to PolicyAgent."""
        # Arrange
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="policy"))]
        mock_openai_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        # Act
        result = await orchestrator.process_message_async(
            session_id="s-001",
            user_message="What is your return policy?",
            modality="text",
        )

        # Assert
        assert result.agent == "policy"
        assert result.intent == "policy"
        assert result.metadata is not None
        mock_policy_agent.process_async.assert_awaited_once()

    async def test_routes_to_chat_agent(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_openai_client: AsyncMock,
        mock_chat_agent: AsyncMock,
    ) -> None:
        """General intent should route to ChatAgent."""
        # Arrange
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="general"))]
        mock_openai_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        # Act
        result = await orchestrator.process_message_async(
            session_id="s-001",
            user_message="Hi there!",
            modality="text",
        )

        # Assert
        assert result.agent == "chat"
        assert result.intent == "general"
        mock_chat_agent.process_async.assert_awaited_once()

    async def test_persists_user_and_assistant_messages(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_openai_client: AsyncMock,
        mock_message_repo: AsyncMock,
    ) -> None:
        """Both user and assistant messages should be persisted."""
        # Arrange
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="general"))]
        mock_openai_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        # Act
        await orchestrator.process_message_async(
            session_id="s-001",
            user_message="Hello",
            modality="text",
        )

        # Assert
        assert mock_message_repo.add_async.await_count == 2
        calls = mock_message_repo.add_async.call_args_list
        assert calls[0].args[0].role == "user"
        assert calls[1].args[0].role == "assistant"
