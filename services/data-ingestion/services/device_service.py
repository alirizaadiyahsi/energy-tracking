"""
Device service for managing device CRUD operations in the database
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import text, select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse

logger = logging.getLogger(__name__)


class DeviceService:
    """Service class for device management operations"""
    
    def __init__(self):
        self.logger = logger

    async def create_device(
        self,
        db: AsyncSession,
        device_data: DeviceCreate,
        created_by: Optional[str] = None
    ) -> DeviceResponse:
        """Create a new device in the database"""
        try:
            # Generate device ID
            device_id = str(uuid.uuid4())
            current_time = datetime.utcnow()
            
            # Prepare device data
            device_dict = device_data.dict()
            device_dict.update({
                "id": device_id,
                "status": "offline",  # Default status
                "created_at": current_time,
                "updated_at": current_time,
                "last_seen": None,
            })
            
            # Add created_by if provided (for audit)
            if created_by:
                device_dict["created_by"] = created_by
            
            # Insert device into database
            query = text("""
                INSERT INTO energy.devices (
                    id, name, device_type, location, description, status,
                    mac_address, ip_address, configuration, metadata,
                    created_at, updated_at, last_seen
                ) VALUES (
                    :id, :name, :device_type, :location, :description, :status,
                    :mac_address, :ip_address, :configuration, :metadata,
                    :created_at, :updated_at, :last_seen
                )
                RETURNING *
            """)
            
            # Convert metadata to JSON string if needed
            metadata_json = device_dict.get("metadata", {})
            configuration_json = device_dict.get("configuration", {})
            
            result = await db.execute(query, {
                "id": device_dict["id"],
                "name": device_dict["name"],
                "device_type": device_dict["device_type"],
                "location": device_dict.get("location"),
                "description": device_dict.get("description"),
                "status": device_dict["status"],
                "mac_address": device_dict.get("mac_address"),
                "ip_address": device_dict.get("ip_address"),
                "configuration": configuration_json,
                "metadata": metadata_json,
                "created_at": device_dict["created_at"],
                "updated_at": device_dict["updated_at"],
                "last_seen": device_dict["last_seen"]
            })
            
            await db.commit()
            
            # Fetch the created device
            created_device = result.first()
            
            self.logger.info(f"Created device: {device_id}")
            
            # Convert to response format
            return DeviceResponse(
                id=created_device.id,
                name=created_device.name,
                device_type=created_device.device_type,
                location=created_device.location,
                description=created_device.description,
                status=created_device.status,
                mac_address=created_device.mac_address,
                ip_address=created_device.ip_address,
                configuration=created_device.configuration or {},
                metadata=created_device.metadata or {},
                last_seen=created_device.last_seen,
                created_at=created_device.created_at,
                updated_at=created_device.updated_at,
                owner_id=str(created_device.owner_id) if created_device.owner_id else None,
                organization_id=str(created_device.organization_id) if created_device.organization_id else None,
                created_by=str(created_device.created_by) if created_device.created_by else None
            )
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Error creating device: {e}")
            raise

    async def get_device(self, db: AsyncSession, device_id: str) -> Optional[DeviceResponse]:
        """Get a device by ID"""
        try:
            query = text("""
                SELECT * FROM energy.devices WHERE id = :device_id
            """)
            
            result = await db.execute(query, {"device_id": device_id})
            device = result.first()
            
            if not device:
                return None
                
            return DeviceResponse(
                id=device.id,
                name=device.name,
                device_type=device.device_type,
                location=device.location,
                description=device.description,
                status=device.status,
                mac_address=device.mac_address,
                ip_address=device.ip_address,
                configuration=device.configuration or {},
                metadata=device.metadata or {},
                last_seen=device.last_seen,
                created_at=device.created_at,
                updated_at=device.updated_at,
                owner_id=str(device.owner_id) if device.owner_id else None,
                organization_id=str(device.organization_id) if device.organization_id else None,
                created_by=str(device.created_by) if device.created_by else None
            )
            
        except Exception as e:
            self.logger.error(f"Error fetching device {device_id}: {e}")
            raise

    async def update_device(
        self,
        db: AsyncSession,
        device_id: str,
        device_data: DeviceUpdate,
        updated_by: Optional[str] = None
    ) -> Optional[DeviceResponse]:
        """Update an existing device"""
        try:
            # Get current device first
            current_device = await self.get_device(db, device_id)
            if not current_device:
                return None
            
            # Prepare update data (only non-None fields)
            update_data = {k: v for k, v in device_data.dict().items() if v is not None}
            update_data["updated_at"] = datetime.utcnow()
            
            if not update_data:
                # No fields to update
                return current_device
            
            # Build dynamic update query
            set_clauses = []
            params = {"device_id": device_id}
            
            for field, value in update_data.items():
                set_clauses.append(f"{field} = :{field}")
                params[field] = value
            
            query = text(f"""
                UPDATE energy.devices 
                SET {', '.join(set_clauses)}
                WHERE id = :device_id
                RETURNING *
            """)
            
            result = await db.execute(query, params)
            await db.commit()
            
            updated_device = result.first()
            
            self.logger.info(f"Updated device: {device_id}")
            
            return DeviceResponse(
                id=updated_device.id,
                name=updated_device.name,
                device_type=updated_device.device_type,
                location=updated_device.location,
                description=updated_device.description,
                status=updated_device.status,
                mac_address=updated_device.mac_address,
                ip_address=updated_device.ip_address,
                configuration=updated_device.configuration or {},
                metadata=updated_device.metadata or {},
                last_seen=updated_device.last_seen,
                created_at=updated_device.created_at,
                updated_at=updated_device.updated_at,
                owner_id=str(updated_device.owner_id) if updated_device.owner_id else None,
                organization_id=str(updated_device.organization_id) if updated_device.organization_id else None,
                created_by=str(updated_device.created_by) if updated_device.created_by else None
            )
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Error updating device {device_id}: {e}")
            raise

    async def delete_device(self, db: AsyncSession, device_id: str) -> bool:
        """Delete a device by ID"""
        try:
            # Check if device exists
            existing_device = await self.get_device(db, device_id)
            if not existing_device:
                return False
            
            # Delete device
            query = text("""
                DELETE FROM energy.devices WHERE id = :device_id
            """)
            
            result = await db.execute(query, {"device_id": device_id})
            await db.commit()
            
            deleted_count = result.rowcount
            
            if deleted_count > 0:
                self.logger.info(f"Deleted device: {device_id}")
                return True
            
            return False
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Error deleting device {device_id}: {e}")
            raise

    async def list_devices(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        device_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[DeviceResponse]:
        """List devices with optional filtering"""
        try:
            # Build query with filters
            where_clauses = []
            params = {"skip": skip, "limit": limit}
            
            if device_type:
                where_clauses.append("device_type = :device_type")
                params["device_type"] = device_type
                
            if status:
                where_clauses.append("status = :status")
                params["status"] = status
            
            where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            query = text(f"""
                SELECT * FROM energy.devices
                {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :skip
            """)
            
            result = await db.execute(query, params)
            devices = result.fetchall()
            
            return [
                DeviceResponse(
                    id=device.id,
                    name=device.name,
                    device_type=device.device_type,
                    location=device.location,
                    description=device.description,
                    status=device.status,
                    mac_address=device.mac_address,
                    ip_address=device.ip_address,
                    configuration=device.configuration or {},
                    metadata=device.metadata or {},
                    last_seen=device.last_seen,
                    created_at=device.created_at,
                    updated_at=device.updated_at,
                    owner_id=str(device.owner_id) if device.owner_id else None,
                    organization_id=str(device.organization_id) if device.organization_id else None,
                    created_by=str(device.created_by) if device.created_by else None
                )
                for device in devices
            ]
            
        except Exception as e:
            self.logger.error(f"Error listing devices: {e}")
            raise


# Global instance
device_service = DeviceService()
