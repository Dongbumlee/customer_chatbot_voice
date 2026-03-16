"""Cosmos DB repositories using sas-cosmosdb Repository Pattern."""

from typing import Optional

from sas.cosmosdb.sql import RepositoryBase

from app.domain.entities import ChatMessage, ChatSession, Product, UserProfile


class ChatSessionRepository(RepositoryBase[ChatSession, str]):
    """Repository for ChatSession entities in the 'chat-sessions' container."""

    def __init__(
        self,
        database_name: str,
        connection_string: Optional[str] = None,
        account_url: Optional[str] = None,
    ) -> None:
        super().__init__(
            connection_string=connection_string,
            account_url=account_url,
            database_name=database_name,
            container_name="chat-sessions",
            use_managed_identity=account_url is not None,
        )


class ChatMessageRepository(RepositoryBase[ChatMessage, str]):
    """Repository for ChatMessage entities in the 'chat-messages' container."""

    def __init__(
        self,
        database_name: str,
        connection_string: Optional[str] = None,
        account_url: Optional[str] = None,
    ) -> None:
        super().__init__(
            connection_string=connection_string,
            account_url=account_url,
            database_name=database_name,
            container_name="chat-messages",
            use_managed_identity=account_url is not None,
        )


class UserProfileRepository(RepositoryBase[UserProfile, str]):
    """Repository for UserProfile entities in the 'user-profiles' container."""

    def __init__(
        self,
        database_name: str,
        connection_string: Optional[str] = None,
        account_url: Optional[str] = None,
    ) -> None:
        super().__init__(
            connection_string=connection_string,
            account_url=account_url,
            database_name=database_name,
            container_name="user-profiles",
            use_managed_identity=account_url is not None,
        )


class ProductRepository(RepositoryBase[Product, str]):
    """Repository for Product entities in the 'products' container."""

    def __init__(
        self,
        database_name: str,
        connection_string: Optional[str] = None,
        account_url: Optional[str] = None,
    ) -> None:
        super().__init__(
            connection_string=connection_string,
            account_url=account_url,
            database_name=database_name,
            container_name="products",
            use_managed_identity=account_url is not None,
        )
