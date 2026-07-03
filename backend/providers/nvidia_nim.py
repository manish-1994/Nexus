from typing import List, Dict, Any, AsyncGenerator
import httpx
from .base import BaseProvider, ProviderType, HealthStatus


class NvidiaNIMProvider(BaseProvider):
  """NVIDIA NIM provider implementation."""

  def get_provider_type(self) -> ProviderType:
    return ProviderType.NVIDIA_NIM

  async def health_check(self) -> HealthStatus:
    """Check NVIDIA NIM API health."""
    if not self.api_key:
      return HealthStatus.INACTIVE
    try:
      async with httpx.AsyncClient() as client:
        base = self.base_url or "https://integrate.api.nvidia.com/v1"
        response = await client.get(
          f"{base}/models",
          headers={"Authorization": f"Bearer {self.api_key}"},
          timeout=10.0,
        )
        if response.status_code == 200:
          return HealthStatus.ACTIVE
        return HealthStatus.ERROR
    except Exception:
      return HealthStatus.ERROR

  async def list_models(self) -> List[Dict[str, Any]]:
    """List available models from NVIDIA NIM."""
    if not self.api_key:
      return []
    try:
      async with httpx.AsyncClient() as client:
        base = self.base_url or "https://integrate.api.nvidia.com/v1"
        response = await client.get(
          f"{base}/models",
          headers={"Authorization": f"Bearer {self.api_key}"},
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
              "supports_streaming": True,
              "supports_vision": "vision" in model_id.lower() or "multimodal" in model_id.lower(),
              "supports_reasoning": "reasoning" in model_id.lower() or "nemotron" in model_id.lower(),
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
      base = self.base_url or "https://integrate.api.nvidia.com/v1"
      response = await client.post(
        f"{base}/chat/completions",
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
      base = self.base_url or "https://integrate.api.nvidia.com/v1"
      async with client.stream(
        "POST",
        f"{base}/chat/completions",
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
