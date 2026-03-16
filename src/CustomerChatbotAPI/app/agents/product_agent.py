"""Product Agent — handles product discovery, recommendations, and comparisons."""

import json
import logging

from openai import AsyncAzureOpenAI

from app.services.product_service import ProductService

logger = logging.getLogger(__name__)


class ProductAgent:
    """Product discovery and recommendation agent.

    Handles product search, comparisons, and recommendations.
    Sources data from Cosmos DB product catalog and Azure AI Search.
    Returns structured product card data alongside text responses.
    """

    SYSTEM_PROMPT = (
        "You are a product specialist assistant. Help users discover products, "
        "compare options, and make recommendations based on their needs. "
        "When showing products, include relevant details like price, features, "
        "and availability. Always ground responses in the product catalog.\n\n"
        "Product catalog context:\n{product_context}"
    )

    def __init__(
        self,
        openai_client: AsyncAzureOpenAI,
        deployment_name: str,
        product_service: ProductService,
    ) -> None:
        self._client = openai_client
        self._deployment = deployment_name
        self._product_service = product_service

    async def process_async(self, message: str, context: dict | None = None) -> dict:
        """Generate a product-focused response with optional product cards.

        Args:
            message: The user's product-related query.
            context: Conversation history and session metadata.

        Returns:
            Dict with 'content' (text) and 'product_cards' (list of product data).
        """
        products = await self._product_service.search_products_async(message)

        product_context = (
            json.dumps(products, default=str)
            if products
            else "No matching products found."
        )
        system_prompt = self.SYSTEM_PROMPT.format(product_context=product_context)

        messages: list[dict] = [{"role": "system", "content": system_prompt}]

        if context and context.get("history"):
            for turn in context["history"][-10:]:
                messages.append({"role": turn["role"], "content": turn["content"]})

        messages.append({"role": "user", "content": f"[User Message]\n{message}\n[End User Message]"})

        response = await self._client.chat.completions.create(
            model=self._deployment,
            messages=messages,
            temperature=0.5,
            max_tokens=1024,
        )

        content = response.choices[0].message.content or ""
        product_cards = [
            {
                "id": p["id"],
                "name": p["name"],
                "category": p["category"],
                "price": p["price"],
                "description": p["description"],
                "image_url": p.get("image_url"),
            }
            for p in products
        ]

        return {"content": content, "product_cards": product_cards}
