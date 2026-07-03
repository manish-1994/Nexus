"""Provider validation service."""
import re
from typing import Optional
from sqlalchemy.orm import Session
from models.provider import Provider, ProviderType
from repositories.provider_repository import ProviderRepository


class ValidationError(Exception):
    """Raised when provider validation fails."""
    pass


class ProviderValidationService:
    """Service for validating provider configuration."""

    # Provider types that don't require API key
    LOCAL_TYPES = {ProviderType.OLLAMA, ProviderType.LMSTUDIO}

    # Provider types that typically require base_url
    CUSTOM_URL_TYPES = {
        ProviderType.OPENAI_COMPATIBLE,
        ProviderType.OLLAMA,
        ProviderType.LMSTUDIO,
        ProviderType.CUSTOM,
    }

    def __init__(self, db: Session):
        self.db = db
        self.repository = ProviderRepository(db)

    def validate_name(self, name: str, exclude_id: Optional[int] = None) -> None:
        """Validate provider name is unique."""
        name = name.strip()
        if not name:
            raise ValidationError("Provider name cannot be empty")
        if len(name) > 255:
            raise ValidationError("Provider name must be 255 characters or less")

        existing = self.repository.find_by_name(name)
        if existing and existing.id != exclude_id:
            raise ValidationError(f"Provider '{name}' already exists")

    def validate_url(self, url: Optional[str], provider_type: str) -> Optional[str]:
        """Validate base URL format."""
        if not url:
            return None

        url = url.strip()
        if not url:
            return None

        # Add https:// if no protocol specified
        if not re.match(r'^https?://', url):
            url = 'https://' + url

        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )

        if not url_pattern.match(url):
            raise ValidationError(f"Invalid URL format: {url}")

        return url

    def validate_api_key(self, api_key: Optional[str], provider_type: str) -> None:
        """Validate API key requirement."""
        try:
            ptype = ProviderType(provider_type)
        except ValueError:
            # Unknown type, require API key to be safe
            if not api_key:
                raise ValidationError("API key is required for this provider type")
            return

        if ptype not in self.LOCAL_TYPES:
            if not api_key:
                raise ValidationError("API key is required for this provider type")

    def validate_provider(
        self,
        name: str,
        provider_type: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        exclude_id: Optional[int] = None,
    ) -> dict:
        """
        Validate provider configuration.
        Returns dict with 'valid' bool and 'errors' list.
        """
        errors = []

        # Validate name
        try:
            self.validate_name(name, exclude_id)
        except ValidationError as e:
            errors.append(str(e))

        # Validate type
        try:
            ProviderType(provider_type)
        except ValueError:
            errors.append(f"Invalid provider type: {provider_type}")

        # Validate URL
        try:
            self.validate_url(base_url, provider_type)
        except ValidationError as e:
            errors.append(str(e))

        # Validate API key
        try:
            self.validate_api_key(api_key, provider_type)
        except ValidationError as e:
            errors.append(str(e))

        return {
            'valid': len(errors) == 0,
            'errors': errors,
        }
