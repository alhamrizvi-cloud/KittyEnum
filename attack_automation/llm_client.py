#!/usr/bin/env python3
"""LLM client wrapper for OpenAI-style providers."""

import os
from typing import Dict, Optional

try:
    import openai
except ImportError:  # pragma: no cover
    openai = None


class LLMClientError(Exception):
    pass


class LLMClient:
    def __init__(self, provider: str = "openai", model: str = "gpt-4o", api_key: Optional[str] = None):
        self.provider = provider
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")

        if self.provider == "openai" and openai is None:
            raise LLMClientError(
                "openai package is not installed. Install optional requirements: attack_automation/requirements.txt"
            )

        if self.api_key is None:
            raise LLMClientError("OPENAI_API_KEY is not configured")

        if self.provider == "openai":
            openai.api_key = self.api_key

    def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.2) -> str:
        if self.provider != "openai":
            raise LLMClientError(f"Unsupported provider: {self.provider}")

        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()

    def summarize(self, context: str) -> str:
        prompt = (
            "You are an attack automation assistant. Summarize this context and suggest the next safe enumeration commands.\n\n"
            f"{context}"
        )
        return self.generate(prompt)
