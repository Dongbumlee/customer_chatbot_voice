"""Cosmos DB repositories using sas-cosmosdb Repository Pattern."""

from sas.cosmosdb.sql import RepositoryBase

from app.domain.entities import ChatMessage, ChatSession, Product, UserProfile


class ChatSessionRepository(RepositoryBase[ChatSession, str]):
    """Repository for ChatSession entities in the 'chat-sessions' container."""

    def __init__(self, connection_string: str, database_name: str) -> None:
        super().__init__(
            connection_string=connection_string,
            database_name=database_name,
            container_name="chat-sessions",
        )


class ChatMessageRepository(RepositoryBase[ChatMessage, str]):
    """Repository for ChatMessage entities in the 'chat-messages' container."""

    def __init__(self, connection_string: str, database_name: str) -> None:
        super().__init__(
            connection_string=connection_string,
            database_name=database_name,
            container_name="chat-messages",
        )


class UserProfileRepository(RepositoryBase[UserProfile, str]):
    """Repository for UserProfile entities in the 'user-profiles' container."""

    def __init__(self, connection_string: str, database_name: str) -> None:
        super().__init__(
            connection_string=connection_string,
            database_name=database_name,
            container_name="user-profiles",
        )


class ProductRepository(RepositoryBase[Product, str]):
    """Repository for Product entities in the 'products' container."""

    def __init__(self, connection_string: str, database_name: str) -> None:
        super().__init__(
            connection_string=connection_string,
            database_name=database_name,
            container_name="products",
        )
