from typing import Generic, TypeVar, Type, List, Optional
from sqlalchemy.orm import Session
from models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """Base repository class for data access."""

    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def find_by_id(self, id: int) -> Optional[ModelType]:
        """Find record by ID."""
        return self.db.query(self.model).filter(self.model.id == id).first()

    def find_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Find all records with pagination."""
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, data: dict) -> ModelType:
        """Create new record."""
        obj = self.model(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, id: int, data: dict) -> Optional[ModelType]:
        """Update existing record."""
        obj = self.find_by_id(id)
        if obj:
            for key, value in data.items():
                setattr(obj, key, value)
            self.db.commit()
            self.db.refresh(obj)
        return obj

    def delete(self, id: int) -> bool:
        """Delete record."""
        obj = self.find_by_id(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False
