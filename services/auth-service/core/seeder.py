"""
Database seeding utilities
"""

import logging

from core.database import get_db
from core.security import SecurityUtils
from models.permission import Permission
from models.role import Role
from models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


class DatabaseSeeder:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def seed_default_admin(self):
        """Create default admin user if it doesn't exist"""
        try:
            # Check if admin user already exists
            result = await self.db.execute(
                select(User).where(User.email == "admin@energy-tracking.com")
            )
            existing_admin = result.scalar_one_or_none()

            if existing_admin:
                logger.info("Default admin user already exists")
                return existing_admin

            # Create default admin user
            admin_user = User(
                email="admin@energy-tracking.com",
                hashed_password=SecurityUtils.hash_password("admin123"),
                full_name="System Administrator",
                is_superuser=True,
                is_active=True,
                status="active",
                email_verified=True,
            )

            self.db.add(admin_user)
            await self.db.commit()
            await self.db.refresh(admin_user)

            logger.info(f"Created default admin user: {admin_user.email}")
            return admin_user

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating default admin user: {e}")
            raise

    async def seed_simple_admin(self):
        """Create a secondary simple admin (admin@mail.com / admin123) if it doesn't exist"""
        try:
            result = await self.db.execute(
                select(User).where(User.email == "admin@mail.com")
            )
            existing = result.scalar_one_or_none()
            if existing:
                logger.info("Simple admin user already exists")
                return existing

            user = User(
                email="admin@mail.com",
                hashed_password=SecurityUtils.hash_password("admin123"),
                full_name="Local Administrator",
                is_superuser=True,
                is_active=True,
                status="active",
                email_verified=True,
            )
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            logger.info("Created simple admin user: admin@mail.com")
            return user
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating simple admin user: {e}")
            raise

    async def seed_default_roles(self):
        """Create default system roles if they don't exist"""
        default_roles = [
            {
                "name": "super_admin",
                "display_name": "Super Administrator",
                "description": "Full system access and management",
                "is_system_role": True,
            },
            {
                "name": "admin",
                "display_name": "Administrator",
                "description": "Organization administration and management",
                "is_system_role": True,
            },
            {
                "name": "manager",
                "display_name": "Manager",
                "description": "Department or team management",
                "is_system_role": True,
            },
            {
                "name": "operator",
                "display_name": "Operator",
                "description": "Device operation and monitoring",
                "is_system_role": True,
            },
            {
                "name": "analyst",
                "display_name": "Data Analyst",
                "description": "Data analysis and reporting",
                "is_system_role": True,
            },
            {
                "name": "viewer",
                "display_name": "Viewer",
                "description": "Read-only access to dashboards and data",
                "is_system_role": True,
            },
        ]

        created_roles = []
        try:
            for role_data in default_roles:
                # Check if role already exists
                result = await self.db.execute(
                    select(Role).where(Role.name == role_data["name"])
                )
                existing_role = result.scalar_one_or_none()

                if existing_role:
                    logger.info(f"Role {role_data['name']} already exists")
                    created_roles.append(existing_role)
                    continue

                # Create new role
                role = Role(**role_data)
                self.db.add(role)
                created_roles.append(role)
                logger.info(f"Created role: {role_data['name']}")

            await self.db.commit()
            return created_roles

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating default roles: {e}")
            raise

    async def seed_default_permissions(self):
        """Create default system permissions if they don't exist"""
        default_permissions = [
            # User management permissions
            {
                "name": "user_create",
                "display_name": "Create Users",
                "description": "Create new user accounts",
                "resource_type": "user",
                "action": "create",
                "is_system_permission": True,
            },
            {
                "name": "user_read",
                "display_name": "View Users",
                "description": "View user information and lists",
                "resource_type": "user",
                "action": "read",
                "is_system_permission": True,
            },
            {
                "name": "user_update",
                "display_name": "Update Users",
                "description": "Modify user accounts and profiles",
                "resource_type": "user",
                "action": "update",
                "is_system_permission": True,
            },
            {
                "name": "user_delete",
                "display_name": "Delete Users",
                "description": "Delete user accounts",
                "resource_type": "user",
                "action": "delete",
                "is_system_permission": True,
            },
            # Device management permissions
            {
                "name": "device_create",
                "display_name": "Create Devices",
                "description": "Add new devices to the system",
                "resource_type": "device",
                "action": "create",
                "is_system_permission": True,
            },
            {
                "name": "device_read",
                "display_name": "View Devices",
                "description": "View device information and status",
                "resource_type": "device",
                "action": "read",
                "is_system_permission": True,
            },
            {
                "name": "device_update",
                "display_name": "Update Devices",
                "description": "Modify device configurations",
                "resource_type": "device",
                "action": "update",
                "is_system_permission": True,
            },
            {
                "name": "device_delete",
                "display_name": "Delete Devices",
                "description": "Remove devices from system",
                "resource_type": "device",
                "action": "delete",
                "is_system_permission": True,
            },
            # Analytics permissions
            {
                "name": "analytics_read",
                "display_name": "View Analytics",
                "description": "View analytics reports and data",
                "resource_type": "analytics",
                "action": "read",
                "is_system_permission": True,
            },
            {
                "name": "analytics_create",
                "display_name": "Create Analytics",
                "description": "Create analytics reports",
                "resource_type": "analytics",
                "action": "create",
                "is_system_permission": True,
            },
            # Dashboard permissions
            {
                "name": "dashboard_read",
                "display_name": "View Dashboards",
                "description": "View dashboards and visualizations",
                "resource_type": "dashboard",
                "action": "read",
                "is_system_permission": True,
            },
            {
                "name": "dashboard_create",
                "display_name": "Create Dashboards",
                "description": "Create custom dashboards",
                "resource_type": "dashboard",
                "action": "create",
                "is_system_permission": True,
            },
            # System permissions
            {
                "name": "system_read",
                "display_name": "View System Info",
                "description": "View system status and configuration",
                "resource_type": "system",
                "action": "read",
                "is_system_permission": True,
            },
            {
                "name": "system_manage",
                "display_name": "Manage System",
                "description": "Full system administration",
                "resource_type": "system",
                "action": "manage",
                "is_system_permission": True,
            },
        ]

        created_permissions = []
        try:
            for perm_data in default_permissions:
                # Check if permission already exists
                result = await self.db.execute(
                    select(Permission).where(Permission.name == perm_data["name"])
                )
                existing_permission = result.scalar_one_or_none()

                if existing_permission:
                    logger.info(f"Permission {perm_data['name']} already exists")
                    created_permissions.append(existing_permission)
                    continue

                # Create new permission
                permission = Permission(**perm_data)
                self.db.add(permission)
                created_permissions.append(permission)
                logger.info(f"Created permission: {perm_data['name']}")

            await self.db.commit()
            return created_permissions

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating default permissions: {e}")
            raise

    async def assign_super_admin_role(self):
        """Assign super_admin role to the default admin user"""
        try:
            # Get admin user with roles loaded
            result = await self.db.execute(
                select(User)
                .options(selectinload(User.roles))
                .where(User.email == "admin@energy-tracking.com")
            )
            admin_user = result.scalar_one_or_none()

            if not admin_user:
                logger.error("Admin user not found")
                return

            # Get super_admin role
            result = await self.db.execute(
                select(Role).where(Role.name == "super_admin")
            )
            super_admin_role = result.scalar_one_or_none()

            if not super_admin_role:
                logger.error("Super admin role not found")
                return

            # Check if already assigned
            if super_admin_role in admin_user.roles:
                logger.info("Admin user already has super_admin role")
                return

            # Assign role
            admin_user.roles.append(super_admin_role)
            await self.db.commit()

            logger.info("Assigned super_admin role to admin user")

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error assigning super_admin role: {e}")
            raise

    async def assign_super_admin_role_simple_admin(self):
        """Assign super_admin role to simple admin user"""
        try:
            result = await self.db.execute(
                select(User).options(selectinload(User.roles)).where(User.email == "admin@mail.com")
            )
            simple_admin = result.scalar_one_or_none()
            if not simple_admin:
                logger.warning("Simple admin user not found when assigning role")
                return

            result = await self.db.execute(select(Role).where(Role.name == "super_admin"))
            super_role = result.scalar_one_or_none()
            if not super_role:
                logger.error("Super admin role not found")
                return

            if super_role in simple_admin.roles:
                logger.info("Simple admin already has super_admin role")
                return

            simple_admin.roles.append(super_role)
            await self.db.commit()
            logger.info("Assigned super_admin role to simple admin user")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error assigning super_admin to simple admin: {e}")
            raise

    async def seed_all(self):
        """Run all seeding operations"""
        logger.info("Starting database seeding...")

        try:
            # Seed in order due to dependencies
            await self.seed_default_permissions()
            await self.seed_default_roles()
            await self.seed_default_admin()
            await self.seed_simple_admin()
            await self.assign_super_admin_role()
            await self.assign_super_admin_role_simple_admin()

            logger.info("Database seeding completed successfully")

        except Exception as e:
            logger.error(f"Database seeding failed: {e}")
            raise


async def run_seeds():
    """Run database seeding - called from startup"""
    try:
        async for db in get_db():
            seeder = DatabaseSeeder(db)
            await seeder.seed_all()
            break  # Only need one iteration
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        raise
