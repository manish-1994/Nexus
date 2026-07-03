from typing import List, Dict, Any, AsyncGenerator
import httpx
from .base import BaseProvider, ProviderType, HealthStatus
import logging


class GeminiProvider(BaseProvider):
    """Gemini provider implementation."""
    logger = logging.getLogger("gemini")

    def get_provider_type(self) -> ProviderType:
        return ProviderType.GEMINI

    async def health_check(self) -> HealthStatus:
        """Check Gemini API health."""
        if not self.api_key:
            return HealthStatus.INACTIVE
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key}",
                    timeout=10.0,
                )
                if response.status_code == 200:
                    return HealthStatus.ACTIVE
                return HealthStatus.ERROR
        except Exception:
            return HealthStatus.ERROR

    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models from Gemini."""
        if not self.api_key:
            return []
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key}",
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    models = []
                    for model in data.get("models", []):
                        name = model.get("name", "").split("/")[-1]
                        models.append({
                            "name": name,
                            "display_name": model.get("displayName", name),
                            "max_tokens": model.get("inputTokenLimit"),
                            "supports_streaming": True,
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
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}],
            })
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}",
                json={
                    "contents": contents,
                    **kwargs,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def stream(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream chat completion."""
        if not self.api_key:
            raise ValueError("API key not configured")
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}],
            })
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse&key={self.api_key}",
                json={
                    "contents": contents,
                    **kwargs,
                },
                timeout=60.0,
            ) as response:
                response.raise_for_status()
                self.logger.info("Gemini stream response status=%s", response.status_code)
                import json
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    # SSE format: lines start with "data: "
                    if line.startswith("data: "):
                        line = line[6:]
                    elif not line.startswith("{"):
                        continue
                    self.logger.info("Gemini stream line: %s", line[:200])
                    try:
                        data = json.loads(line)
                        if "candidates" in data and len(data["candidates"]) > 0:
                            candidate = data["candidates"][0]
                            if "content" in candidate and "parts" in candidate["content"]:
                                for part in candidate["content"]["parts"]:
                                    part_text = part.get("text", "")
                                    if part_text:
                                        self.logger.info("Gemini stream yielding text len=%s", len(part_text))
                                        yield part_text
                    except json.JSONDecodeError as e:
                        self.logger.warning("Gemini stream JSON parse error: %s, line: %s", e, line[:200])
