"""
Device service for managing device CRUD operations in the database
"""

import logging
import json
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
                    metadata, created_at, updated_at, last_seen
                ) VALUES (
                    :id, :name, :device_type, :location, :description, :status,
                    :metadata, :created_at, :updated_at, :last_seen
                )
                RETURNING *
            """)
            
            # Convert metadata to JSON string if needed
            metadata_json = device_dict.get("metadata", {})
            if isinstance(metadata_json, dict):
                metadata_json = json.dumps(metadata_json)
            
            result = await db.execute(query, {
                "id": device_dict["id"],
                "name": device_dict["name"],
                "device_type": device_dict["type"],
                "location": device_dict.get("location"),
                "description": device_dict.get("description"),
                "status": device_dict["status"],
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
                id=str(created_device.id),
                name=created_device.name,
                type=created_device.device_type,
                location=created_device.location,
                description=created_device.description,
                status=created_device.status,
                metadata=created_device.metadata or {},
                created_at=created_device.created_at,
                updated_at=created_device.updated_at,
                last_seen=created_device.last_seen
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
                id=str(device.id),
                name=device.name,
                type=device.device_type,
                location=device.location,
                description=device.description,
                status=device.status,
                metadata=device.metadata or {},
                created_at=device.created_at,
                updated_at=device.updated_at,
                last_seen=device.last_seen
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
            
            # Build dynamic update query with proper field mapping
            set_clauses = []
            params = {"device_id": device_id}
            
            # Map fields to database column names
            field_mapping = {
                "type": "device_type",
                "name": "name", 
                "location": "location",
                "description": "description",
                "status": "status",
                "metadata": "metadata",
                "updated_at": "updated_at"
            }
            
            for field, value in update_data.items():
                db_field = field_mapping.get(field, field)
                set_clauses.append(f"{db_field} = :{field}")
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
                id=str(updated_device.id),
                name=updated_device.name,
                type=updated_device.device_type,
                location=updated_device.location,
                description=updated_device.description,
                status=updated_device.status,
                metadata=updated_device.metadata or {},
                created_at=updated_device.created_at,
                updated_at=updated_device.updated_at,
                last_seen=updated_device.last_seen
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
                    id=str(device.id),
                    name=device.name,
                    type=device.device_type,
                    location=device.location,
                    description=device.description,
                    status=device.status,
                    metadata=device.metadata or {},
                    created_at=device.created_at,
                    updated_at=device.updated_at,
                    last_seen=device.last_seen
                )
                for device in devices
            ]
            
        except Exception as e:
            self.logger.error(f"Error listing devices: {e}")
            raise


# Global instance
device_service = DeviceService()
