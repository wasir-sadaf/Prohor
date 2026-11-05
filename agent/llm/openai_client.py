"""
OpenAI LLM backend.

Uses the official ``openai`` Python SDK with the Responses API.
The dependency is imported lazily so that the agent can import this
module without the package when a different provider is active.
"""

from __future__ import annotations

from agent.schemas.message import ChatMessage


class OpenAIClient:
    """
    Thin wrapper around the OpenAI Responses API.

    Adapts the Responses API output to the existing LLMClient
    interface (``chat() -> str``).
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-6-luna",
        temperature: float = 0.3,
        max_tokens: int = 2048,
        timeout: int = 30,
    ) -> None:
        from openai import OpenAI  # type: ignore

        self._client = OpenAI(api_key=api_key, timeout=timeout)
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    def chat(self, messages: list[ChatMessage]) -> str:
        """
        Send messages to the OpenAI Responses API and return text.

        Converts the internal ``ChatMessage`` list to the format
        expected by the Responses API, calls the endpoint, and
        extracts the text output.
        """
        # ── Build the input for the Responses API ───────────────
        # The Responses API accepts a list of input items.
        # System messages become top-level instructions.
        input_items: list[dict] = []
        instructions: str | None = None

        for msg in messages:
            if msg.role == "system":
                # Accumulate system messages as instructions
                if instructions:
                    instructions += "\n\n" + msg.content
                else:
                    instructions = msg.content
            else:
                input_items.append({
                    "role": msg.role,
                    "content": msg.content,
                })

        # ── Call the Responses API ────────────────────────────────
        kwargs: dict = {
            "model": self._model,
            "input": input_items,
        }
        if instructions:
            kwargs["instructions"] = instructions

        # max_output_tokens is the Responses API parameter name
        kwargs["max_output_tokens"] = self._max_tokens
        kwargs["temperature"] = self._temperature

        response = self._client.responses.create(**kwargs)

        # ── Extract text from the response ───────────────────────
        # The Responses API returns output as a list of items.
        # Text output is typically in the first output_text item.
        output_text = ""
        if hasattr(response, "output_text") and response.output_text:
            output_text = response.output_text
        elif hasattr(response, "output") and response.output:
            for item in response.output:
                if hasattr(item, "content"):
                    for content_item in item.content:
                        if hasattr(content_item, "text"):
                            output_text += content_item.text
                elif hasattr(item, "text"):
                    output_text += item.text

        return output_text

    @property
    def model_name(self) -> str:
        return self._model
