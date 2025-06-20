"""Base model for database entities."""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class BaseModel(SQLModel):
    """Base model with common fields for all database entities."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
