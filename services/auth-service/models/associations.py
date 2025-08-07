from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from core.database import Base

# Association table for many-to-many relationship between users and roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('auth.users.id'), primary_key=True),
    Column('role_id', UUID(as_uuid=True), ForeignKey('auth.roles.id'), primary_key=True),
    schema='auth'
)

# Association table for many-to-many relationship between roles and permissions
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', UUID(as_uuid=True), ForeignKey('auth.roles.id'), primary_key=True),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('auth.permissions.id'), primary_key=True),
    schema='auth'
)
