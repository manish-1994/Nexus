from typing import List, Dict, Any, AsyncGenerator
import httpx
from .base import BaseProvider, ProviderType, HealthStatus


class AnthropicProvider(BaseProvider):
  """Anthropic provider implementation."""

  def get_provider_type(self) -> ProviderType:
    return ProviderType.ANTHROPIC

  async def health_check(self) -> HealthStatus:
    """Check Anthropic API health."""
    if not self.api_key:
      return HealthStatus.INACTIVE
    try:
      async with httpx.AsyncClient() as client:
        response = await client.get(
          "https://api.anthropic.com/v1/models",
          headers={
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
          },
          timeout=10.0,
        )
        if response.status_code == 200:
          return HealthStatus.ACTIVE
        return HealthStatus.ERROR
    except Exception:
      return HealthStatus.ERROR

  async def list_models(self) -> List[Dict[str, Any]]:
    """List available models from Anthropic."""
    if not self.api_key:
      return []
    try:
      async with httpx.AsyncClient() as client:
        response = await client.get(
          "https://api.anthropic.com/v1/models",
          headers={
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
          },
          timeout=10.0,
        )
        if response.status_code == 200:
          data = response.json()
          models = []
          for model in data.get("data", []):
            model_id = model.get("id", "")
            models.append({
              "name": model_id,
              "display_name": model.get("display_name", model_id),
              "max_tokens": model.get("context_length") or model.get("max_tokens"),
              "supports_streaming": True,
              "supports_vision": "vision" in model.get("id", "").lower() or "claude-3" in model_id.lower(),
              "supports_reasoning": "claude-3" in model_id.lower() or "claude-2" in model_id.lower(),
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
        "https://api.anthropic.com/v1/messages",
        headers={
          "x-api-key": self.api_key,
          "anthropic-version": "2023-06-01",
          "Content-Type": "application/json",
        },
        json={
          "model": model,
          "messages": messages,
          "max_tokens": kwargs.get("max_tokens", 4096),
          **{k: v for k, v in kwargs.items() if k != "max_tokens"},
        },
        timeout=60.0,
      )
      response.raise_for_status()
      data = response.json()
      return data["content"][0]["text"]

  async def stream(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> AsyncGenerator[str, None]:
    """Stream chat completion."""
    if not self.api_key:
      raise ValueError("API key not configured")
    async with httpx.AsyncClient() as client:
      async with client.stream(
        "POST",
        "https://api.anthropic.com/v1/messages",
        headers={
          "x-api-key": self.api_key,
          "anthropic-version": "2023-06-01",
          "Content-Type": "application/json",
        },
        json={
          "model": model,
          "messages": messages,
          "stream": True,
          "max_tokens": kwargs.get("max_tokens", 4096),
          **{k: v for k, v in kwargs.items() if k != "max_tokens"},
        },
        timeout=60.0,
      ) as response:
        response.raise_for_status()
        async for line in response.aiter_lines():
          line = line.strip()
          if line.startswith("data: "):
            data = line[6:]
            try:
              import json
              chunk = json.loads(data)
              if chunk.get("type") == "content_block_delta":
                yield chunk.get("delta", {}).get("text", "")
            except Exception:
              continue
