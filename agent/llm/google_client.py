"""
Google / Gemini LLM backend.

Uses the ``google-generativeai`` package. Imported lazily so the
agent works without it when using the mock backend.
"""

from __future__ import annotations

from agent.schemas.message import ChatMessage


class GoogleLLMClient:
    """Thin wrapper around the Google Gemini API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
        temperature: float = 0.3,
        max_tokens: int = 2048,
        timeout: int = 30,
    ) -> None:
        import google.generativeai as genai  # type: ignore

        genai.configure(api_key=api_key)
        self._genai = genai
        self._model_name = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    def chat(self, messages: list[ChatMessage]) -> str:
        # Convert to Gemini's chat format
        contents = []
        for msg in messages:
            role = "user" if msg.role == "user" else "model"
            if msg.role == "system":
                role = "user"  # Gemini doesn't have a system role
            contents.append({"role": role, "parts": [msg.content]})

        model = self._genai.GenerativeModel(
            self._model_name,
            generation_config={
                "temperature": self._temperature,
                "max_output_tokens": self._max_tokens,
            },
        )
        response = model.generate_content(contents)
        return response.text or ""

    @property
    def model_name(self) -> str:
        return self._model_name
