from typing import List, Dict, Any, AsyncGenerator
import httpx
from .base import BaseProvider, ProviderType, HealthStatus


class OpenRouterProvider(BaseProvider):
    """OpenRouter provider implementation."""

    def get_provider_type(self) -> ProviderType:
        return ProviderType.OPENROUTER

    async def health_check(self) -> HealthStatus:
        """Check OpenRouter API health."""
        if not self.api_key:
            return HealthStatus.INACTIVE
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10.0,
                )
                if response.status_code == 200:
                    return HealthStatus.ACTIVE
                return HealthStatus.ERROR
        except Exception:
            return HealthStatus.ERROR

    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models from OpenRouter."""
        if not self.api_key:
            return []
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    models = []
                    for model in data.get("data", []):
                        sp = model.get("supported_parameters")
                        streaming_val = True
                        if isinstance(sp, dict):
                            streaming_val = sp.get("stream", True)
                        elif isinstance(sp, list):
                            streaming_val = "stream" in sp
                        models.append({
                            "name": model.get("id"),
                            "display_name": model.get("name"),
                            "max_tokens": model.get("context_length"),
                            "supports_streaming": streaming_val,
                            "description": model.get("description"),
                        })
                    return models
                return []
        except Exception:
            return []

    async def chat(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> str:
        """Send chat completion request."""
        if not self.api_key:
            raise ValueError("API key not configured")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    **kwargs,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def stream(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream chat completion."""
        if not self.api_key:
            raise ValueError("API key not configured")
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "stream": True,
                    **kwargs,
                },
                timeout=60.0,
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
