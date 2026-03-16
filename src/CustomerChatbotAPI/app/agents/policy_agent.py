"""Policy Agent — handles returns, warranty, FAQ, and business policy queries."""

import json
import logging

from openai import AsyncAzureOpenAI

from app.services.policy_service import PolicyService

logger = logging.getLogger(__name__)


class PolicyAgent:
    """Policy and FAQ agent.

    Handles questions about return policies, warranties, shipping,
    and general business FAQ. Uses RAG over policy documents in
    Blob Storage via Azure AI Search.
    """

    SYSTEM_PROMPT = (
        "You are a policy and FAQ specialist. Answer questions about "
        "return policies, warranties, shipping, and business procedures. "
        "Ground all answers in official policy documents. If a policy "
        "does not exist for the question, say so clearly.\n\n"
        "Policy context:\n{policy_context}"
    )

    def __init__(
        self,
        openai_client: AsyncAzureOpenAI,
        deployment_name: str,
        policy_service: PolicyService,
    ) -> None:
        self._client = openai_client
        self._deployment = deployment_name
        self._policy_service = policy_service

    async def process_async(self, message: str, context: dict | None = None) -> dict:
        """Generate a policy-focused response grounded in source documents.

        Args:
            message: The user's policy-related question.
            context: Conversation history and session metadata.

        Returns:
            Dict with 'content' (text) and optional source references.
        """
        policies = await self._policy_service.search_policies_async(message)

        policy_context = (
            json.dumps(policies, default=str)
            if policies
            else "No matching policy documents found."
        )
        system_prompt = self.SYSTEM_PROMPT.format(policy_context=policy_context)

        messages: list[dict] = [{"role": "system", "content": system_prompt}]

        if context and context.get("history"):
            for turn in context["history"][-10:]:
                messages.append({"role": turn["role"], "content": turn["content"]})

        messages.append({"role": "user", "content": f"[User Message]\n{message}\n[End User Message]"})

        response = await self._client.chat.completions.create(
            model=self._deployment,
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )

        content = response.choices[0].message.content or ""
        sources = [
            {"title": p.get("title", ""), "source": p.get("source", "")}
            for p in policies
        ]

        return {"content": content, "sources": sources}
