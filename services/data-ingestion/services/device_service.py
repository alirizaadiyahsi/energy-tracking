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
        # Import here to avoid circular imports
        from services.device_event_publisher import device_event_publisher
        self.event_publisher = device_event_publisher
        self.logger = logger

    async def create_device(
        self,
        db: AsyncSession,
        device_data: DeviceCreate,
        created_by: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> DeviceResponse:
        """Create a new device in the database"""
        try:
            # Generate device ID
            device_id = str(uuid.uuid4())
            current_time = datetime.utcnow()
            
            # Prepare device data
            device_dict = device_data.model_dump()
            device_dict.update({
                "id": device_id,
                "status": "offline",  # Default status
                "created_at": current_time,
                "updated_at": current_time,
                "last_seen": None,
                "organization_id": organization_id
            })
            
            # Insert device into database (simplified - organization_id may not exist in current schema)
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
            device_response = DeviceResponse(
                id=str(created_device.id),
                name=created_device.name,
                type=created_device.device_type,
                location=created_device.location,
                description=created_device.description,
                status=created_device.status,
                base_power=None,  # Not in DB yet
                base_voltage=None,  # Not in DB yet
                firmware_version=None,  # Not in DB yet
                model=None,  # Not in DB yet
                metadata=created_device.metadata or {},
                created_at=created_device.created_at,
                updated_at=created_device.updated_at,
                last_seen=created_device.last_seen
            )
            
            # Publish device created event
            self.logger.error("DEBUG: About to publish device created event")
            try:
                # Convert device response to dict and handle datetime serialization
                device_dict = device_response.model_dump()
                self.logger.info(f"Converting device response to dict for device {device_id}")
                # Convert datetime objects to ISO strings for JSON serialization
                for key, value in device_dict.items():
                    if hasattr(value, 'isoformat'):  # datetime objects
                        device_dict[key] = value.isoformat() + "Z" if value else None
                
                self.logger.error(f"DEBUG: Calling event_publisher.publish_device_created for device {device_id}")
                await self.event_publisher.publish_device_created(
                    device_id=device_id,
                    device_data=device_dict
                )
                self.logger.error(f"DEBUG: Successfully called event_publisher.publish_device_created for device {device_id}")
            except Exception as e:
                self.logger.warning(f"Failed to publish device created event: {e}")
                import traceback
                self.logger.warning(f"Traceback: {traceback.format_exc()}")
            
            return device_response
            
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
                base_power=None,  # Not in DB yet
                base_voltage=None,  # Not in DB yet
                firmware_version=None,  # Not in DB yet
                model=None,  # Not in DB yet
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
            update_data = {k: v for k, v in device_data.model_dump().items() if v is not None}
            update_data["updated_at"] = datetime.utcnow()
            
            if not update_data:
                # No fields to update
                return current_device
            
            # Build dynamic update query with proper field mapping
            set_clauses = []
            params = {"device_id": device_id}
            
            # Map fields to database column names (only include existing columns)
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
                # Only include fields that exist in database
                if field in field_mapping:
                    db_field = field_mapping[field]
                    set_clauses.append(f"{db_field} = :{field}")
                    
                    # Handle JSON serialization for metadata
                    if field == "metadata" and isinstance(value, dict):
                        params[field] = json.dumps(value)
                    else:
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
            
            device_response = DeviceResponse(
                id=str(updated_device.id),
                name=updated_device.name,
                type=updated_device.device_type,
                location=updated_device.location,
                description=updated_device.description,
                status=updated_device.status,
                base_power=None,  # Not in DB yet
                base_voltage=None,  # Not in DB yet
                firmware_version=None,  # Not in DB yet
                model=None,  # Not in DB yet
                metadata=updated_device.metadata or {},
                created_at=updated_device.created_at,
                updated_at=updated_device.updated_at,
                last_seen=updated_device.last_seen
            )
            
            # Publish device updated event
            try:
                # Convert device response to dict and handle datetime serialization
                device_dict = device_response.model_dump()
                # Convert datetime objects to ISO strings for JSON serialization
                for key, value in device_dict.items():
                    if hasattr(value, 'isoformat'):  # datetime objects
                        device_dict[key] = value.isoformat() + "Z" if value else None
                
                await self.event_publisher.publish_device_updated(
                    device_id=device_id,
                    device_data=device_dict
                )
            except Exception as e:
                self.logger.warning(f"Failed to publish device updated event: {e}")
            
            return device_response
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Error updating device {device_id}: {e}")
            raise

    async def delete_device(self, db: AsyncSession, device_id: str) -> bool:
        """Delete a device by ID"""
        try:
            # Check if device exists and get its data for the event
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
                
                # Publish device deleted event
                try:
                    # Convert device response to dict and handle datetime serialization
                    device_dict = existing_device.model_dump()
                    # Convert datetime objects to ISO strings for JSON serialization
                    for key, value in device_dict.items():
                        if hasattr(value, 'isoformat'):  # datetime objects
                            device_dict[key] = value.isoformat() + "Z" if value else None
                    
                    await self.event_publisher.publish_device_deleted(
                        device_id=device_id,
                        device_data=device_dict
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to publish device deleted event: {e}")
                
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
        status: Optional[str] = None,
        organization_filter: Optional[str] = None
    ) -> List[DeviceResponse]:
        """List devices with optional filtering and organization access control"""
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
            
            # Add organization filter if provided (for access control)
            if organization_filter:
                where_clauses.append(f"({organization_filter})")
            
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
                    base_power=None,  # Not in DB yet
                    base_voltage=None,  # Not in DB yet
                    firmware_version=None,  # Not in DB yet
                    model=None,  # Not in DB yet
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
