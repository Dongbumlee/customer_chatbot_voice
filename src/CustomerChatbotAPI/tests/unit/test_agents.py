"""Unit tests for Chat, Product, and Policy agents."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.chat_agent import ChatAgent
from app.agents.policy_agent import PolicyAgent
from app.agents.product_agent import ProductAgent


@pytest.fixture
def mock_openai_client() -> AsyncMock:
    """Create a mock AsyncAzureOpenAI client."""
    client = AsyncMock()
    return client


def _make_openai_response(content: str) -> MagicMock:
    """Helper to create a mock OpenAI chat completion response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=content))]
    return mock_response


class TestChatAgent:
    """Tests for the ChatAgent."""

    @pytest.fixture
    def chat_agent(self, mock_openai_client: AsyncMock) -> ChatAgent:
        return ChatAgent(
            openai_client=mock_openai_client,
            deployment_name="gpt-4o",
        )

    async def test_process_returns_response_text(
        self, chat_agent: ChatAgent, mock_openai_client: AsyncMock,
    ) -> None:
        """ChatAgent should return the model's response text."""
        # Arrange
        mock_openai_client.chat.completions.create = AsyncMock(
            return_value=_make_openai_response("Hello! How can I help?"),
        )

        # Act
        result = await chat_agent.process_async("Hi!")

        # Assert
        assert result == "Hello! How can I help?"
        mock_openai_client.chat.completions.create.assert_awaited_once()

    async def test_process_includes_context_history(
        self, chat_agent: ChatAgent, mock_openai_client: AsyncMock,
    ) -> None:
        """ChatAgent should include conversation history in the prompt."""
        # Arrange
        mock_openai_client.chat.completions.create = AsyncMock(
            return_value=_make_openai_response("Sure, I remember!"),
        )
        context = {
            "history": [
                {"role": "user", "content": "My name is Alice"},
                {"role": "assistant", "content": "Nice to meet you, Alice!"},
            ],
        }

        # Act
        result = await chat_agent.process_async("Do you remember my name?", context)

        # Assert
        assert result == "Sure, I remember!"
        call_kwargs = mock_openai_client.chat.completions.create.call_args.kwargs
        messages = call_kwargs["messages"]
        assert len(messages) == 4  # system + 2 history + user
        assert messages[1]["content"] == "My name is Alice"

    async def test_process_handles_empty_response(
        self, chat_agent: ChatAgent, mock_openai_client: AsyncMock,
    ) -> None:
        """ChatAgent should return empty string for None content."""
        # Arrange
        mock_openai_client.chat.completions.create = AsyncMock(
            return_value=_make_openai_response(None),
        )

        # Act
        result = await chat_agent.process_async("Test")

        # Assert
        assert result == ""


class TestProductAgent:
    """Tests for the ProductAgent."""

    @pytest.fixture
    def mock_product_service(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def product_agent(
        self, mock_openai_client: AsyncMock, mock_product_service: AsyncMock,
    ) -> ProductAgent:
        return ProductAgent(
            openai_client=mock_openai_client,
            deployment_name="gpt-4o",
            product_service=mock_product_service,
        )

    async def test_process_returns_content_and_cards(
        self,
        product_agent: ProductAgent,
        mock_openai_client: AsyncMock,
        mock_product_service: AsyncMock,
    ) -> None:
        """ProductAgent should return content and product cards."""
        # Arrange
        mock_product_service.search_products_async = AsyncMock(return_value=[
            {"id": "p1", "name": "Widget", "category": "tools", "price": 9.99, "description": "A widget", "image_url": None},
        ])
        mock_openai_client.chat.completions.create = AsyncMock(
            return_value=_make_openai_response("Check out this widget!"),
        )

        # Act
        result = await product_agent.process_async("Show me widgets")

        # Assert
        assert result["content"] == "Check out this widget!"
        assert len(result["product_cards"]) == 1
        assert result["product_cards"][0]["name"] == "Widget"

    async def test_process_with_no_products_found(
        self,
        product_agent: ProductAgent,
        mock_openai_client: AsyncMock,
        mock_product_service: AsyncMock,
    ) -> None:
        """ProductAgent should handle empty search results."""
        # Arrange
        mock_product_service.search_products_async = AsyncMock(return_value=[])
        mock_openai_client.chat.completions.create = AsyncMock(
            return_value=_make_openai_response("Sorry, no products found."),
        )

        # Act
        result = await product_agent.process_async("Show me unicorns")

        # Assert
        assert result["content"] == "Sorry, no products found."
        assert result["product_cards"] == []


class TestPolicyAgent:
    """Tests for the PolicyAgent."""

    @pytest.fixture
    def mock_policy_service(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def policy_agent(
        self, mock_openai_client: AsyncMock, mock_policy_service: AsyncMock,
    ) -> PolicyAgent:
        return PolicyAgent(
            openai_client=mock_openai_client,
            deployment_name="gpt-4o",
            policy_service=mock_policy_service,
        )

    async def test_process_returns_content_and_sources(
        self,
        policy_agent: PolicyAgent,
        mock_openai_client: AsyncMock,
        mock_policy_service: AsyncMock,
    ) -> None:
        """PolicyAgent should return grounded content with sources."""
        # Arrange
        mock_policy_service.search_policies_async = AsyncMock(return_value=[
            {"id": "pol-1", "title": "Return Policy", "content": "30-day returns", "source": "returns.md"},
        ])
        mock_openai_client.chat.completions.create = AsyncMock(
            return_value=_make_openai_response("You can return items within 30 days."),
        )

        # Act
        result = await policy_agent.process_async("What is your return policy?")

        # Assert
        assert "30 days" in result["content"]
        assert len(result["sources"]) == 1
        assert result["sources"][0]["title"] == "Return Policy"

    async def test_process_with_no_policies_found(
        self,
        policy_agent: PolicyAgent,
        mock_openai_client: AsyncMock,
        mock_policy_service: AsyncMock,
    ) -> None:
        """PolicyAgent should handle no matching policies gracefully."""
        # Arrange
        mock_policy_service.search_policies_async = AsyncMock(return_value=[])
        mock_openai_client.chat.completions.create = AsyncMock(
            return_value=_make_openai_response("I couldn't find a policy for that."),
        )

        # Act
        result = await policy_agent.process_async("Can I return a spaceship?")

        # Assert
        assert result["content"] == "I couldn't find a policy for that."
        assert result["sources"] == []
