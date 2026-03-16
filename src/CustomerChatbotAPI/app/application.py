"""Application configuration and settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Azure Cosmos DB
    cosmos_connection_string: str = ""
    cosmos_database_name: str = "customer-chatbot"

    # Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_api_version: str = "2024-12-01-preview"

    # Azure AI Foundry
    azure_ai_project_connection_string: str = ""

    # Azure AI Search
    azure_search_endpoint: str = ""
    azure_search_index_name: str = "products-policies"

    # Azure Blob Storage
    azure_storage_account_name: str = ""

    # Azure Key Vault
    azure_keyvault_url: str = ""

    # Azure Voice Live API
    azure_voice_endpoint: str = ""
    azure_voice_key: str = ""
    azure_voice_region: str = "eastus2"

    # Authentication
    azure_tenant_id: str = ""
    azure_client_id: str = ""
    allowed_origins: list[str] = ["http://localhost:5173"]

    # Application
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
