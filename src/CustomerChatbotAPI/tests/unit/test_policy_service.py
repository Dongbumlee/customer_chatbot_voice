"""Unit tests for PolicyService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.services.policy_service import PolicyService


@pytest.fixture
def mock_search_client() -> AsyncMock:
    """Create a mock Azure AI SearchClient."""
    return AsyncMock()


@pytest.fixture
def policy_service(mock_search_client: AsyncMock) -> PolicyService:
    """Create a PolicyService with mocked dependencies."""
    return PolicyService(
        storage_account_name="teststorage",
        search_client=mock_search_client,
    )


class TestGetPolicyDocument:
    """Tests for get_policy_document_async."""

    async def test_returns_document_content(
        self,
        policy_service: PolicyService,
    ) -> None:
        """Should return document content as string."""
        # Arrange
        mock_helper = AsyncMock()
        mock_helper.download_blob = AsyncMock(
            return_value=b"# Return Policy\nAll items can be returned within 30 days.",
        )
        mock_helper.__aenter__ = AsyncMock(return_value=mock_helper)
        mock_helper.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.services.policy_service.AsyncStorageBlobHelper",
            return_value=mock_helper,
        ):
            # Act
            result = await policy_service.get_policy_document_async("returns-policy.md")

        # Assert
        assert result is not None
        assert "Return Policy" in result
        assert "30 days" in result

    async def test_returns_none_when_not_found(
        self,
        policy_service: PolicyService,
    ) -> None:
        """Should return None when blob does not exist."""
        # Arrange
        mock_helper = AsyncMock()
        mock_helper.download_blob = AsyncMock(side_effect=Exception("Blob not found"))
        mock_helper.__aenter__ = AsyncMock(return_value=mock_helper)
        mock_helper.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.services.policy_service.AsyncStorageBlobHelper",
            return_value=mock_helper,
        ):
            # Act
            result = await policy_service.get_policy_document_async("nonexistent.md")

        # Assert
        assert result is None


class TestSearchPolicies:
    """Tests for search_policies_async."""

    async def test_returns_matching_policies(
        self,
        policy_service: PolicyService,
        mock_search_client: AsyncMock,
    ) -> None:
        """Should return policy excerpts from search results."""
        # Arrange
        search_results = [
            {
                "id": "pol-001",
                "title": "Return Policy",
                "content": "Items can be returned within 30 days.",
                "source": "returns-policy.md",
                "@search.score": 0.92,
            },
        ]

        async def mock_search_iter():
            for item in search_results:
                yield item

        mock_search_client.search = MagicMock(return_value=mock_search_iter())

        # Act
        results = await policy_service.search_policies_async("return policy")

        # Assert
        assert len(results) == 1
        assert results[0]["title"] == "Return Policy"
        assert results[0]["source"] == "returns-policy.md"

    async def test_returns_empty_list_on_error(
        self,
        policy_service: PolicyService,
        mock_search_client: AsyncMock,
    ) -> None:
        """Should return empty list when search fails."""
        # Arrange
        mock_search_client.search = MagicMock(side_effect=Exception("Search error"))

        # Act
        results = await policy_service.search_policies_async("warranty")

        # Assert
        assert results == []
