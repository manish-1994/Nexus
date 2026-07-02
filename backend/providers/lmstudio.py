from typing import List, Dict, Any, AsyncGenerator
import httpx
from .base import BaseProvider, ProviderType, HealthStatus


class LMStudioProvider(BaseProvider):
    """LM Studio provider implementation."""

    def get_provider_type(self) -> ProviderType:
        return ProviderType.LMSTUDIO

    async def health_check(self) -> HealthStatus:
        """Check LM Studio server health."""
        base_url = self.base_url or "http://localhost:1234"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/v1/models",
                    timeout=5.0,
                )
                if response.status_code == 200:
                    return HealthStatus.ACTIVE
                return HealthStatus.ERROR
        except Exception:
            return HealthStatus.ERROR

    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models from LM Studio."""
        base_url = self.base_url or "http://localhost:1234"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/v1/models",
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    models = []
                    for model in data.get("data", []):
                        models.append({
                            "name": model.get("id"),
                            "display_name": model.get("id"),
                            "max_tokens": model.get("context_length"),
                            "supports_streaming": True,
                            "description": model.get("description"),
                        })
                    return models
                return []
        except Exception:
            return []

    async def chat(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> str:
        """Send chat completion request."""
        base_url = self.base_url or "http://localhost:1234"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/v1/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    **kwargs,
                },
                timeout=120.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def stream(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream chat completion."""
        base_url = self.base_url or "http://localhost:1234"
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{base_url}/v1/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": True,
                    **kwargs,
                },
                timeout=120.0,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            import json
                            chunk = json.loads(data)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
