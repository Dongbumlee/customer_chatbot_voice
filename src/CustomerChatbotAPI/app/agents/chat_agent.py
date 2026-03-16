"""Chat Agent — handles general conversation, greetings, and fallback."""

import logging

from openai import AsyncAzureOpenAI

logger = logging.getLogger(__name__)


class ChatAgent:
    """General conversation agent.

    Handles greetings, small talk, clarification requests,
    and serves as fallback when intent is ambiguous.
    Uses GPT-4o via Azure OpenAI for response generation.
    """

    SYSTEM_PROMPT = (
        "You are a friendly and helpful customer service assistant. "
        "You handle general conversation, greetings, and questions that "
        "don't fall into product or policy categories. "
        "Always identify yourself as an AI assistant."
    )

    def __init__(
        self,
        openai_client: AsyncAzureOpenAI,
        deployment_name: str,
    ) -> None:
        self._client = openai_client
        self._deployment = deployment_name

    async def process_async(self, message: str, context: dict | None = None) -> str:
        """Generate a response for a general conversation message.

        Args:
            message: The user's input text.
            context: Conversation history and session metadata.

        Returns:
            Agent response text.
        """
        messages: list[dict] = [{"role": "system", "content": self.SYSTEM_PROMPT}]

        if context and context.get("history"):
            for turn in context["history"][-10:]:
                messages.append({"role": turn["role"], "content": turn["content"]})

        messages.append({
            "role": "user",
            "content": f"[User Message]\n{message}\n[End User Message]",
        })

        response = await self._client.chat.completions.create(
            model=self._deployment,
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
        )

        return response.choices[0].message.content or ""
