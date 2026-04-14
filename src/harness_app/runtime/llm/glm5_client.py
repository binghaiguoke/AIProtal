from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from harness_app.foundation.config_center.settings import LlmBackendConfig


@dataclass(slots=True)
class LlmGenerationResult:
    content: str
    provider_trace_id: str = ""
    raw_model: str = ""


class Glm5Client:
    def __init__(self, config: LlmBackendConfig) -> None:
        self._config = config

    @property
    def provider(self) -> str:
        return self._config.provider

    @property
    def model(self) -> str:
        return self._config.model

    @property
    def endpoint(self) -> str:
        return f"{self._config.api_base_url}/chat/completions"

    @property
    def is_configured(self) -> bool:
        return bool(self._config.api_key.strip())

    def generate(self, *, system_prompt: str, messages: list[dict[str, Any]]) -> LlmGenerationResult:
        if not self.is_configured:
            raise RuntimeError("SiliconFlow API key is not configured")

        payload = {
            "model": self._config.model,
            "messages": [{"role": "system", "content": system_prompt}, *messages],
            "temperature": self._config.temperature,
            "max_tokens": self._config.max_tokens,
            "stream": False,
        }
        response = httpx.post(
            self.endpoint,
            headers={
                "Authorization": f"Bearer {self._config.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self._config.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("SiliconFlow response did not contain choices")
        message = choices[0].get("message", {})
        content = message.get("content", "")
        text = ""
        if isinstance(content, list):
            text = "\n".join(
                str(item.get("text", "")) for item in content if isinstance(item, dict) and item.get("text")
            ).strip()
        else:
            text = str(content).strip()
        return LlmGenerationResult(
            content=text,
            provider_trace_id=response.headers.get("x-siliconcloud-trace-id", ""),
            raw_model=str(data.get("model", self._config.model)),
        )
