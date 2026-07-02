from sqlalchemy import Column, Integer, DateTime, func
from datetime import datetime
from database import Base


class BaseModel(Base):
    """Base model with common fields."""
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
