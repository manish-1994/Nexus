from typing import List, Dict, Any, AsyncGenerator
import httpx
import json
import logging
from .base import BaseProvider, ProviderType, HealthStatus

logger = logging.getLogger("openai_compatible")


class OpenAICompatibleProvider(BaseProvider):
    """Generic provider for OpenAI-compatible APIs."""

    PROVIDER_CONFIGS = {
        "openrouter": {
            "base_url": "https://openrouter.ai/api/v1",
            "chat_path": "/chat/completions",
            "models_path": "/models",
        },
        "groq": {
            "base_url": "https://api.groq.com/openai/v1",
            "chat_path": "/chat/completions",
            "models_path": "/models",
        },
        "ollama": {
            "base_url": "http://localhost:11434/v1",
            "chat_path": "/chat/completions",
            "models_path": "/models",
        },
        "lmstudio": {
            "base_url": "http://localhost:1234/v1",
            "chat_path": "/chat/completions",
            "models_path": "/models",
        },
    }

    def __init__(self, api_key: str = None, base_url: str = None, provider_type: str = None, **kwargs):
        super().__init__(api_key=api_key, base_url=base_url)
        self.provider_type = provider_type
        config = self.PROVIDER_CONFIGS.get(provider_type, {})
        self.base_url = (base_url or config.get("base_url", "http://localhost:8000")).rstrip("/")
        self.chat_path = config.get("chat_path", "/chat/completions")
        self.models_path = config.get("models_path", "/models")
        self.timeout = kwargs.get("timeout", 60)
        self.custom_headers = kwargs.get("custom_headers", {})

    def get_provider_type(self) -> ProviderType:
        return ProviderType.OPENAI_COMPATIBLE

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if self.custom_headers:
            headers.update(self.custom_headers)
        return headers

    async def health_check(self) -> HealthStatus:
        if not self.api_key:
            return HealthStatus.INACTIVE
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}{self.models_path}",
                    headers=self._headers(),
                    timeout=10.0,
                )
                if response.status_code == 200:
                    return HealthStatus.ACTIVE
                return HealthStatus.ERROR
        except Exception:
            return HealthStatus.ERROR

    async def list_models(self) -> List[Dict[str, Any]]:
        if not self.api_key:
            return []
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}{self.models_path}",
                    headers=self._headers(),
                    timeout=10.0,
                )
                if response.status_code != 200:
                    return []
                data = response.json()
                models = []
                for model in data.get("data", []):
                    models.append({
                        "name": model.get("id"),
                        "display_name": model.get("name", model.get("id")),
                        "max_tokens": model.get("context_length") or model.get("context_window"),
                        "supports_streaming": True,
                        "description": model.get("description"),
                    })
                return models
        except Exception:
            return []

    async def chat(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> str:
        if not self.api_key:
            raise ValueError("API key not configured")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{self.chat_path}",
                headers=self._headers(),
                json={
                    "model": model,
                    "messages": messages,
                    **kwargs,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def stream(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> AsyncGenerator[str, None]:
        if not self.api_key:
            raise ValueError("API key not configured")
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}{self.chat_path}",
                headers=self._headers(),
                json={
                    "model": model,
                    "messages": messages,
                    "stream": True,
                    **kwargs,
                },
                timeout=self.timeout,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        if "choices" in chunk and len(chunk["choices"]) > 0:
                            delta = chunk["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                    except json.JSONDecodeError:
                        continue
