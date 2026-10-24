"""
SQLAlchemy declarative base and model mixins.
All database models inherit from Base.
"""

from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import DateTime
from datetime import datetime
from typing import Any

# Declarative base for all models
Base = declarative_base()


class BaseModel(Base):
    """
    Abstract base class for all database models with common fields.
    """
    __abstract__ = True
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        doc="Record creation timestamp (UTC)"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        doc="Record last update timestamp (UTC)"
    )
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<{self.__class__.__name__}>"
