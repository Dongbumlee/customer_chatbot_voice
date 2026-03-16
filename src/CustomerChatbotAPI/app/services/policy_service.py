"""Policy service — retrieves and formats policy documents from Blob Storage."""

import logging

from azure.search.documents.aio import SearchClient
from sas.storage.blob import AsyncStorageBlobHelper

logger = logging.getLogger(__name__)


class PolicyService:
    """Handles policy document retrieval and search.

    Uses Blob Storage (via sas-storage) for raw document access
    and Azure AI Search for semantic policy lookup.
    """

    def __init__(
        self,
        storage_account_name: str,
        search_client: SearchClient,
    ) -> None:
        self._storage_account_name = storage_account_name
        self._search_client = search_client

    async def get_policy_document_async(self, document_name: str) -> str | None:
        """Retrieve a policy document by name from Blob Storage.

        Args:
            document_name: Blob name (e.g., 'returns-policy.md').

        Returns:
            Document content as string, or None if not found.
        """
        try:
            async with AsyncStorageBlobHelper(
                account_name=self._storage_account_name,
            ) as helper:
                data = await helper.download_blob("policies", document_name)
                if isinstance(data, bytes):
                    return data.decode("utf-8")
                return str(data)
        except Exception:
            logger.exception(
                "Failed to retrieve policy document: %s",
                document_name,
            )
            return None

    async def search_policies_async(self, query: str, top: int = 3) -> list[dict]:
        """Search policy documents using AI Search.

        Args:
            query: Natural-language policy question.
            top: Maximum number of results.

        Returns:
            List of relevant policy excerpts.
        """
        try:
            results = self._search_client.search(
                search_text=query,
                top=top,
                select=["id", "title", "content", "source"],
            )
            policies = []
            async for result in results:
                policies.append({
                    "id": result["id"],
                    "title": result.get("title", ""),
                    "content": result.get("content", ""),
                    "source": result.get("source", ""),
                    "score": result.get("@search.score", 0),
                })
            return policies
        except Exception:
            logger.exception("Policy search failed for query: %s", query)
            return []
