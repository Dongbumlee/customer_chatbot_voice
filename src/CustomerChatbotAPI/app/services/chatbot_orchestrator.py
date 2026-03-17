"""Chatbot orchestrator — routes user messages to domain-specific agents."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Literal

from openai import AsyncAzureOpenAI

from app.agents.chat_agent import ChatAgent
from app.agents.policy_agent import PolicyAgent
from app.agents.product_agent import ProductAgent
from app.domain.entities import ChatMessage
from app.domain.enums import Intent
from app.domain.models import AgentResponse
from app.infrastructure.repositories import ChatMessageRepository, ChatSessionRepository

logger = logging.getLogger(__name__)

INTENT_SYSTEM_PROMPT = (
    "Classify the user message intent into exactly one category.\n"
    "Respond with ONLY one word: product, policy, or general.\n\n"
    "- product: questions about products, pricing, recommendations, comparisons, availability\n"
    "- policy: questions about returns, warranties, shipping, refunds, business rules\n"
    "- general: greetings, small talk, unclear requests, anything else"
)


class ChatbotOrchestrator:
    """Routes user messages to domain-specific agents via intent classification.

    Uses intent classification to dispatch to Chat, Product, or Policy agents.
    Manages conversation context and response aggregation.
    """

    def __init__(
        self,
        openai_client: AsyncAzureOpenAI,
        deployment_name: str,
        chat_agent: ChatAgent,
        product_agent: ProductAgent,
        policy_agent: PolicyAgent,
        session_repository: ChatSessionRepository,
        message_repository: ChatMessageRepository,
    ) -> None:
        self._client = openai_client
        self._deployment = deployment_name
        self._chat_agent = chat_agent
        self._product_agent = product_agent
        self._policy_agent = policy_agent
        self._session_repo = session_repository
        self._message_repo = message_repository

    async def process_message_async(
        self,
        session_id: str,
        user_message: str,
        modality: Literal["text", "voice"],
    ) -> AgentResponse:
        """Process a user message and return an agent response.

        Args:
            session_id: The active chat session ID.
            user_message: The user's text input (or transcribed voice).
            modality: Whether the input came from text or voice.

        Returns:
            Structured agent response with content and metadata.
        """
        intent = await self.classify_intent_async(user_message)
        context = await self._build_context_async(session_id)

        if intent == Intent.PRODUCT:
            result = await self._product_agent.process_async(user_message, context)
            agent_name = "product"
            content = result["content"]
            product_cards = result.get("product_cards")
            metadata = None
        elif intent == Intent.POLICY:
            result = await self._policy_agent.process_async(user_message, context)
            agent_name = "policy"
            content = result["content"]
            product_cards = None
            metadata = {"sources": result.get("sources", [])}
        else:
            content = await self._chat_agent.process_async(user_message, context)
            agent_name = "chat"
            product_cards = None
            metadata = None

        now = datetime.now(timezone.utc)

        user_msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=user_message,
            modality=modality,
            timestamp=now,
        )
        await self._message_repo.add_async(user_msg)

        assistant_msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="assistant",
            content=content,
            modality=modality,
            agent=agent_name,
            metadata={"product_cards": product_cards} if product_cards else metadata,
            timestamp=now,
        )
        await self._message_repo.add_async(assistant_msg)

        try:
            session = await self._session_repo.get_async(session_id)
            if session:
                session.last_active_at = now
                await self._session_repo.update_async(session)
        except Exception:
            logger.warning("Failed to update session timestamp for %s", session_id)

        return AgentResponse(
            content=content,
            agent=agent_name,
            intent=intent.value,
            product_cards=product_cards,
            metadata=metadata,
        )

    async def process_message_stream_async(
        self,
        session_id: str,
        user_message: str,
        modality: Literal["text", "voice"] = "text",
    ):
        """Stream agent response tokens. Yields dicts with type and data.

        First yields metadata (agent, intent), then content chunks, then done.
        """
        intent = await self.classify_intent_async(user_message)
        context = await self._build_context_async(session_id)

        now = datetime.now(timezone.utc)
        user_msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=user_message,
            modality=modality,
            timestamp=now,
        )
        await self._message_repo.add_async(user_msg)

        if intent == Intent.GENERAL:
            agent_name = "chat"
            yield {"type": "meta", "agent": agent_name, "intent": intent.value}

            full_content = ""
            async for chunk in self._chat_agent.process_stream_async(
                user_message, context
            ):
                full_content += chunk
                yield {"type": "chunk", "content": chunk}

            yield {"type": "done"}

            assistant_msg = ChatMessage(
                id=str(uuid.uuid4()),
                session_id=session_id,
                role="assistant",
                content=full_content,
                modality=modality,
                agent=agent_name,
                timestamp=datetime.now(timezone.utc),
            )
            await self._message_repo.add_async(assistant_msg)
        else:
            # Product and Policy agents aren't streamed (they need search results first)
            response = await self.process_message_async(
                session_id, user_message, modality
            )
            yield {"type": "meta", "agent": response.agent, "intent": response.intent}
            yield {"type": "chunk", "content": response.content}
            if response.product_cards:
                yield {"type": "product_cards", "cards": response.product_cards}
            if response.metadata:
                yield {"type": "metadata", "data": response.metadata}
            yield {"type": "done"}

    async def classify_intent_async(self, message: str) -> Intent:
        """Classify user intent to determine which agent handles the message.

        Args:
            message: The user's input text.

        Returns:
            Classified intent (product, policy, or general).
        """
        response = await self._client.chat.completions.create(
            model=self._deployment,
            messages=[
                {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            temperature=0.0,
            max_tokens=10,
        )

        raw = (response.choices[0].message.content or "").strip().lower()

        if raw == "product":
            return Intent.PRODUCT
        if raw == "policy":
            return Intent.POLICY
        return Intent.GENERAL

    async def _build_context_async(self, session_id: str) -> dict:
        """Build conversation context from recent messages."""
        try:
            messages = await self._message_repo.find_async(
                {"session_id": session_id},
            )
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in (messages or [])[-20:]
            ]
            return {"history": history}
        except Exception:
            logger.warning("Failed to load context for session %s", session_id)
            return {"history": []}
