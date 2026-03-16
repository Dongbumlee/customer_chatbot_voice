"""Product service — product catalog lookup and search."""

import logging

from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizableTextQuery

from app.infrastructure.repositories import ProductRepository

logger = logging.getLogger(__name__)


class ProductService:
    """Handles product discovery, search, and catalog operations.

    Uses Cosmos DB (via sas-cosmosdb) for structured queries
    and Azure AI Search for semantic product search.
    """

    def __init__(
        self,
        product_repository: ProductRepository,
        search_client: SearchClient,
    ) -> None:
        self._repository = product_repository
        self._search_client = search_client

    async def get_product_async(self, product_id: str) -> dict | None:
        """Get a product by ID.

        Args:
            product_id: The product identifier.

        Returns:
            Product data or None if not found.
        """
        try:
            entity = await self._repository.get_async(product_id)
            if entity is None:
                return None
            return entity.model_dump()
        except Exception:
            logger.exception("Failed to get product %s", product_id)
            return None

    async def search_products_async(self, query: str, top: int = 5) -> list[dict]:
        """Search products using AI Search for semantic matching.

        Args:
            query: Natural-language product search query.
            top: Maximum number of results to return.

        Returns:
            List of matching products with relevance scores.
        """
        try:
            vector_query = VectorizableTextQuery(
                text=query,
                k_nearest_neighbors=top,
                fields="description_vector",
            )
            results = self._search_client.search(
                search_text=query,
                vector_queries=[vector_query],
                top=top,
                select=["id", "name", "category", "price", "description", "image_url"],
            )
            products = []
            async for result in results:
                products.append({
                    "id": result["id"],
                    "name": result["name"],
                    "category": result["category"],
                    "price": result["price"],
                    "description": result["description"],
                    "image_url": result.get("image_url"),
                    "score": result.get("@search.score", 0),
                })
            return products
        except Exception:
            logger.exception("Product search failed for query: %s", query)
            return []
