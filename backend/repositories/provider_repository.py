from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from models.provider import Provider, ProviderType
from repositories.base_repository import BaseRepository


class ProviderRepository(BaseRepository[Provider]):
    """Repository for provider data access."""

    def __init__(self, db: Session):
        super().__init__(Provider, db)

    def find_by_name(self, name: str) -> Optional[Provider]:
        """Find provider by name."""
        return self.db.query(Provider).filter(Provider.name == name).first()

    def find_by_type(self, provider_type: ProviderType) -> List[Provider]:
        """Find providers by type."""
        return self.db.query(Provider).filter(Provider.type == provider_type).all()

    def find_active(self) -> List[Provider]:
        """Find all active providers."""
        return self.db.query(Provider).options(joinedload(Provider.models)).filter(Provider.is_active == True).all()

    def find_all(self, skip: int = 0, limit: int = 100) -> List[Provider]:
        """Find all providers with models eagerly loaded."""
        return self.db.query(Provider).options(joinedload(Provider.models)).offset(skip).limit(limit).all()
