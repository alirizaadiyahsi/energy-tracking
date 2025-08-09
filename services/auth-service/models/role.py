import uuid
from datetime import datetime

from core.database import Base
from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .associations import role_permissions, user_roles


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    is_system_role = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)

    # relationships
    permissions = relationship(
        "Permission", secondary=role_permissions, back_populates="roles"
    )
    users = relationship("User", secondary=user_roles, back_populates="roles")
