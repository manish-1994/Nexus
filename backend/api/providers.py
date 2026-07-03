from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from database import get_db
from services.provider_service import ProviderService
from schemas.provider import ProviderCreate, ProviderUpdate, ProviderResponse, ModelResponse
from models.provider import ProviderType

router = APIRouter()


def get_provider_service(db: Session = Depends(get_db)) -> ProviderService:
    """Get provider service instance."""
    return ProviderService(db)


@router.get("/providers", response_model=List[ProviderResponse])
async def list_providers(service: ProviderService = Depends(get_provider_service)):
    """List all providers."""
    providers = service.get_all_providers()
    for p in providers:
        print(f"[Backend] Provider ID: {p.id}, Name: {p.name}, Models Count: {len(p.models) if hasattr(p, 'models') else 'N/A'}")
        if hasattr(p, 'models') and p.models:
            print(f"[Backend]   First model: {p.models[0].name}")
    return providers


@router.post("/providers", response_model=ProviderResponse, status_code=201)
async def create_provider(provider_in: ProviderCreate, service: ProviderService = Depends(get_provider_service)):
    """Create a new provider."""
    return service.create_provider(provider_in.model_dump())


@router.get("/providers/{provider_id}", response_model=ProviderResponse)
async def get_provider(provider_id: int, service: ProviderService = Depends(get_provider_service)):
    """Get provider by ID."""
    provider = service.get_provider_by_id(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@router.put("/providers/{provider_id}", response_model=ProviderResponse)
async def update_provider(provider_id: int, provider_in: ProviderUpdate, service: ProviderService = Depends(get_provider_service)):
    """Update provider."""
    provider = service.update_provider(provider_id, provider_in.model_dump())
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@router.delete("/providers/{provider_id}", status_code=204)
async def delete_provider(provider_id: int, service: ProviderService = Depends(get_provider_service)):
    """Delete provider."""
    success = service.delete_provider(provider_id)
    if not success:
        raise HTTPException(status_code=404, detail="Provider not found")
    return None


@router.post("/providers/{provider_id}/test")
async def test_provider_connection(provider_id: int, service: ProviderService = Depends(get_provider_service)):
    """Test provider connection."""
    result = await service.test_connection(provider_id)
    return result


@router.post("/providers/{provider_id}/models", response_model=List[ModelResponse])
async def discover_models(provider_id: int, service: ProviderService = Depends(get_provider_service)):
    """Discover models from provider."""
    return await service.discover_models(provider_id)


@router.get("/providers/{provider_id}/models", response_model=List[ModelResponse])
async def list_models(provider_id: int, service: ProviderService = Depends(get_provider_service)):
    """List models for a provider."""
    return service.get_models_by_provider(provider_id)


@router.delete("/providers/{provider_id}/models/{model_id}", status_code=204)
async def delete_model(provider_id: int, model_id: int, service: ProviderService = Depends(get_provider_service)):
  """Delete a model."""
  success = service.delete_model(model_id)
  if not success:
    raise HTTPException(status_code=404, detail="Model not found")
  return None


class ProviderValidationRequest(BaseModel):
  name: str
  type: str
  base_url: Optional[str] = None
  api_key: Optional[str] = None


class ProviderValidationResponse(BaseModel):
  valid: bool
  errors: List[str]


@router.post("/providers/validate", response_model=ProviderValidationResponse)
async def validate_provider_config(
  request: ProviderValidationRequest,
  service: ProviderService = Depends(get_provider_service),
):
  """Validate provider configuration without creating/updating."""
  result = service.validate_provider_config(
    name=request.name,
    provider_type=request.type,
    base_url=request.base_url,
    api_key=request.api_key,
  )
  return ProviderValidationResponse(**result)
