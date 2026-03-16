"""FastAPI application entry point for the Customer Chatbot API."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.search.documents.aio import SearchClient
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncAzureOpenAI

from app.agents.chat_agent import ChatAgent
from app.agents.policy_agent import PolicyAgent
from app.agents.product_agent import ProductAgent
from app.application import get_settings
from app.infrastructure.repositories import (
    ChatMessageRepository,
    ChatSessionRepository,
    ProductRepository,
    UserProfileRepository,
)
from app.routers import chat_router, http_probes, product_router, voice_router
from app.services.chatbot_orchestrator import ChatbotOrchestrator
from app.services.policy_service import PolicyService
from app.services.product_service import ProductService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan — initialise and tear down shared resources."""
    settings = get_settings()
    openai_client = None
    product_search_client = None
    policy_search_client = None

    try:
        credential = DefaultAzureCredential()

        # Repositories — prefer managed identity (account_url), fall back to connection string
        repo_kwargs = {"database_name": settings.cosmos_database_name}
        if settings.cosmos_account_url:
            repo_kwargs["account_url"] = settings.cosmos_account_url
        else:
            repo_kwargs["connection_string"] = settings.cosmos_connection_string

        app.state.session_repository = ChatSessionRepository(**repo_kwargs)
        app.state.message_repository = ChatMessageRepository(**repo_kwargs)
        app.state.product_repository = ProductRepository(**repo_kwargs)
        app.state.user_profile_repository = UserProfileRepository(**repo_kwargs)

        # AI Search clients
        product_search_client = SearchClient(
            endpoint=settings.azure_search_endpoint,
            index_name="products",
            credential=credential,
        )
        policy_search_client = SearchClient(
            endpoint=settings.azure_search_endpoint,
            index_name="policies",
            credential=credential,
        )

        # OpenAI client
        token_provider = get_bearer_token_provider(
            credential,
            "https://cognitiveservices.azure.com/.default",
        )
        openai_client = AsyncAzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            azure_ad_token_provider=token_provider,
            api_version=settings.azure_openai_api_version,
        )

        # Services
        app.state.product_service = ProductService(
            product_repository=app.state.product_repository,
            search_client=product_search_client,
        )
        policy_service = PolicyService(
            storage_account_name=settings.azure_storage_account_name,
            search_client=policy_search_client,
        )
        app.state.voice_service = None
        if settings.azure_voice_resource_name:
            from app.services.voice_service import VoiceService

            app.state.voice_service = VoiceService(
                resource_name=settings.azure_voice_resource_name,
                model=settings.azure_voice_model,
            )
            logger.info("Voice Live API enabled (resource: %s)", settings.azure_voice_resource_name)
        else:
            logger.warning("Voice Live resource not configured — voice features disabled")

        # Agents
        chat_agent = ChatAgent(
            openai_client=openai_client,
            deployment_name=settings.azure_openai_deployment,
        )
        product_agent = ProductAgent(
            openai_client=openai_client,
            deployment_name=settings.azure_openai_deployment,
            product_service=app.state.product_service,
        )
        policy_agent = PolicyAgent(
            openai_client=openai_client,
            deployment_name=settings.azure_openai_deployment,
            policy_service=policy_service,
        )

        # Orchestrator
        app.state.orchestrator = ChatbotOrchestrator(
            openai_client=openai_client,
            deployment_name=settings.azure_openai_deployment,
            chat_agent=chat_agent,
            product_agent=product_agent,
            policy_agent=policy_agent,
            session_repository=app.state.session_repository,
            message_repository=app.state.message_repository,
        )

        logger.info("Application initialized")
    except Exception:
        logger.exception("Failed to initialize application — running in degraded mode")
        app.state.orchestrator = None
        app.state.voice_service = None
        app.state.product_service = None

    yield

    # Cleanup
    try:
        if product_search_client:
            await product_search_client.close()
        if policy_search_client:
            await policy_search_client.close()
        if openai_client:
            await openai_client.close()
    except Exception:
        pass
    logger.info("Application shut down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Customer Chatbot API",
        description="Multi-agent conversational AI with voice integration",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # Register routers
    app.include_router(http_probes.router)
    app.include_router(chat_router.router, prefix="/api/chat", tags=["chat"])
    app.include_router(voice_router.router, prefix="/api/voice", tags=["voice"])
    app.include_router(product_router.router, prefix="/api/products", tags=["products"])

    return app


app = create_app()
