"""Application configuration and settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Azure Cosmos DB
    cosmos_connection_string: str = ""
    cosmos_account_url: str = ""
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
    azure_ad_client_id: str = ""
    allowed_origins: str = "http://localhost:5173"

    # Application
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def cors_origins(self) -> list[str]:
        """Parse allowed_origins as comma-separated or JSON list."""
        import json
        val = self.allowed_origins.strip()
        if not val:
            return ["http://localhost:5173"]
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return [str(o) for o in parsed]
        except (json.JSONDecodeError, TypeError):
            pass
        return [o.strip() for o in val.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
