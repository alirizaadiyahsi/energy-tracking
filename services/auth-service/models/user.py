import uuid
from datetime import datetime

from core.database import Base
from pydantic import BaseModel
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import relationship

from .associations import user_roles


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    department = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    status = Column(
        ENUM(
            "active", "inactive", "suspended", "pending_activation", name="user_status"
        ),
        default="pending_activation",
    )
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, default=datetime.utcnow)
    email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(255), nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)

    # relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")

    @property
    def first_name(self) -> str:
        """Extract first name from full_name"""
        if self.full_name:
            return self.full_name.split()[0] if self.full_name.split() else ""
        return ""

    @property
    def last_name(self) -> str:
        """Extract last name from full_name"""
        if self.full_name:
            parts = self.full_name.split()
            return " ".join(parts[1:]) if len(parts) > 1 else ""
        return ""

    @property
    def is_verified(self) -> bool:
        """Alias for email_verified for compatibility"""
        return self.email_verified
