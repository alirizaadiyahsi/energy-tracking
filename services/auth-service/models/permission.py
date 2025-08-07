from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.orm import relationship
import uuid
from core.database import Base
from datetime import datetime
from .associations import role_permissions

class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    resource_type = Column(ENUM('device', 'device_group', 'user', 'role', 'alert', 'analytics', 'dashboard', 'system', name='resource_type'), nullable=False)
    action = Column(ENUM('create', 'read', 'update', 'delete', 'execute', 'manage', name='permission_action'), nullable=False)
    conditions = Column(JSONB, default={})
    is_system_permission = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
