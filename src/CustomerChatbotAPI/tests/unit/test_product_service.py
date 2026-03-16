"""Unit tests for ProductService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.entities import Product
from app.services.product_service import ProductService


@pytest.fixture
def mock_product_repository() -> AsyncMock:
    """Create a mock ProductRepository."""
    return AsyncMock()


@pytest.fixture
def mock_search_client() -> AsyncMock:
    """Create a mock Azure AI SearchClient."""
    return AsyncMock()


@pytest.fixture
def product_service(
    mock_product_repository: AsyncMock,
    mock_search_client: AsyncMock,
) -> ProductService:
    """Create a ProductService with mocked dependencies."""
    return ProductService(
        product_repository=mock_product_repository,
        search_client=mock_search_client,
    )


class TestGetProduct:
    """Tests for get_product_async."""

    async def test_returns_product_when_found(
        self,
        product_service: ProductService,
        mock_product_repository: AsyncMock,
    ) -> None:
        """Should return product dict when entity exists."""
        # Arrange
        product = Product(
            id="prod-001",
            name="Headphones",
            category="electronics",
            price=79.99,
            description="Wireless headphones",
        )
        mock_product_repository.get_async = AsyncMock(return_value=product)

        # Act
        result = await product_service.get_product_async("prod-001")

        # Assert
        assert result is not None
        assert result["id"] == "prod-001"
        assert result["name"] == "Headphones"
        assert result["price"] == 79.99
        mock_product_repository.get_async.assert_awaited_once_with("prod-001")

    async def test_returns_none_when_not_found(
        self,
        product_service: ProductService,
        mock_product_repository: AsyncMock,
    ) -> None:
        """Should return None when product does not exist."""
        # Arrange
        mock_product_repository.get_async = AsyncMock(return_value=None)

        # Act
        result = await product_service.get_product_async("nonexistent")

        # Assert
        assert result is None

    async def test_returns_none_on_repository_error(
        self,
        product_service: ProductService,
        mock_product_repository: AsyncMock,
    ) -> None:
        """Should return None and log error on repository failure."""
        # Arrange
        mock_product_repository.get_async = AsyncMock(side_effect=Exception("DB error"))

        # Act
        result = await product_service.get_product_async("prod-001")

        # Assert
        assert result is None


class TestSearchProducts:
    """Tests for search_products_async."""

    async def test_returns_matching_products(
        self,
        product_service: ProductService,
        mock_search_client: AsyncMock,
    ) -> None:
        """Should return list of products from search results."""
        # Arrange
        search_result = [
            {
                "id": "prod-001",
                "name": "Headphones",
                "category": "electronics",
                "price": 79.99,
                "description": "Wireless headphones",
                "image_url": "https://example.com/hp.jpg",
                "@search.score": 0.95,
            },
        ]

        async def mock_search_iter():
            for item in search_result:
                yield item

        mock_search_client.search = MagicMock(return_value=mock_search_iter())

        # Act
        results = await product_service.search_products_async("headphones")

        # Assert
        assert len(results) == 1
        assert results[0]["id"] == "prod-001"
        assert results[0]["score"] == 0.95

    async def test_returns_empty_list_on_no_results(
        self,
        product_service: ProductService,
        mock_search_client: AsyncMock,
    ) -> None:
        """Should return empty list when no products match."""
        # Arrange
        async def mock_empty_iter():
            return
            yield  # noqa: unreachable — makes this an async generator

        mock_search_client.search = MagicMock(return_value=mock_empty_iter())

        # Act
        results = await product_service.search_products_async("nonexistent")

        # Assert
        assert results == []

    async def test_returns_empty_list_on_search_error(
        self,
        product_service: ProductService,
        mock_search_client: AsyncMock,
    ) -> None:
        """Should return empty list and handle search errors gracefully."""
        # Arrange
        mock_search_client.search = MagicMock(side_effect=Exception("Search error"))

        # Act
        results = await product_service.search_products_async("headphones")

        # Assert
        assert results == []
