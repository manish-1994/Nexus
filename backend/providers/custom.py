from typing import List, Dict, Any, AsyncGenerator
import httpx
from .base import BaseProvider, ProviderType, HealthStatus


class CustomProvider(BaseProvider):
  """Custom provider implementation for user-defined endpoints."""

  def get_provider_type(self) -> ProviderType:
    return ProviderType.CUSTOM

  async def health_check(self) -> HealthStatus:
    """Check custom provider health."""
    if not self.base_url:
      return HealthStatus.INACTIVE
    try:
      async with httpx.AsyncClient() as client:
        response = await client.get(
          f"{self.base_url}/models",
          timeout=10.0,
        )
        if response.status_code == 200:
          return HealthStatus.ACTIVE
        return HealthStatus.ERROR
    except Exception:
      return HealthStatus.ERROR

  async def list_models(self) -> List[Dict[str, Any]]:
    """List available models from custom provider."""
    if not self.base_url:
      return []
    try:
      async with httpx.AsyncClient() as client:
        headers = {}
        if self.api_key:
          headers["Authorization"] = f"Bearer {self.api_key}"
        response = await client.get(
          f"{self.base_url}/models",
          headers=headers,
          timeout=10.0,
        )
        if response.status_code == 200:
          data = response.json()
          models = []
          for model in data.get("data", []):
            model_id = model.get("id", "")
            models.append({
              "name": model_id,
              "display_name": model.get("name", model_id),
              "max_tokens": model.get("context_length") or model.get("max_tokens"),
              "supports_streaming": model.get("stream", True),
              "supports_vision": model.get("vision", False),
              "supports_reasoning": model.get("reasoning", False),
              "description": model.get("description"),
            })
          return models
        return []
    except Exception:
      return []

  async def chat(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> str:
    """Send chat completion request."""
    if not self.base_url:
      raise ValueError("Base URL not configured")
    async with httpx.AsyncClient() as client:
      headers = {"Content-Type": "application/json"}
      if self.api_key:
        headers["Authorization"] = f"Bearer {self.api_key}"
      response = await client.post(
        f"{self.base_url}/chat/completions",
        headers=headers,
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
    if not self.base_url:
      raise ValueError("Base URL not configured")
    async with httpx.AsyncClient() as client:
      headers = {"Content-Type": "application/json"}
      if self.api_key:
        headers["Authorization"] = f"Bearer {self.api_key}"
      async with client.stream(
        "POST",
        f"{self.base_url}/chat/completions",
        headers=headers,
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
          line = line.strip()
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
            except Exception:
              continue
