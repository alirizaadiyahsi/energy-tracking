import uuid
from datetime import datetime

from core.database import Base
from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import relationship

from .associations import role_permissions


class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    resource_type = Column(
        ENUM(
            "device",
            "device_group",
            "user",
            "role",
            "alert",
            "analytics",
            "dashboard",
            "system",
            name="resource_type",
        ),
        nullable=False,
    )
    action = Column(
        ENUM(
            "create",
            "read",
            "update",
            "delete",
            "execute",
            "manage",
            name="permission_action",
        ),
        nullable=False,
    )
    conditions = Column(JSONB, default={})
    is_system_permission = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    roles = relationship(
        "Role", secondary=role_permissions, back_populates="permissions"
    )
