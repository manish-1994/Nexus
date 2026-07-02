from typing import List, Dict, Any, AsyncGenerator
import httpx
from .base import BaseProvider, ProviderType, HealthStatus


class OllamaProvider(BaseProvider):
    """Ollama provider implementation."""

    def get_provider_type(self) -> ProviderType:
        return ProviderType.OLLAMA

    async def health_check(self) -> HealthStatus:
        """Check Ollama server health."""
        base_url = self.base_url or "http://localhost:11434"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/api/tags",
                    timeout=5.0,
                )
                if response.status_code == 200:
                    return HealthStatus.ACTIVE
                return HealthStatus.ERROR
        except Exception:
            return HealthStatus.ERROR

    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models from Ollama."""
        base_url = self.base_url or "http://localhost:11434"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/api/tags",
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    models = []
                    for model in data.get("models", []):
                        models.append({
                            "name": model.get("name"),
                            "display_name": model.get("name"),
                            "max_tokens": model.get("details", {}).get("parameter_size"),
                            "supports_streaming": True,
                            "description": model.get("description"),
                        })
                    return models
                return []
        except Exception:
            return []

    async def chat(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> str:
        """Send chat completion request."""
        base_url = self.base_url or "http://localhost:11434"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/chat",
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
            return data.get("message", {}).get("content", "")

    async def stream(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream chat completion."""
        base_url = self.base_url or "http://localhost:11434"
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{base_url}/api/chat",
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
                    if line:
                        try:
                            import json
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
                        except json.JSONDecodeError:
                            continue
