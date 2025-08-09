"""
Database utilities for common database operations
"""

import asyncio
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import IntegrityError
from .exceptions import ResourceNotFoundError, ResourceConflictError

T = TypeVar('T', bound=DeclarativeBase)


class BaseRepository(Generic[T]):
    """Base repository class for common database operations"""
    
    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model
    
    async def create(self, **kwargs) -> T:
        """Create a new record"""
        try:
            instance = self.model(**kwargs)
            self.session.add(instance)
            await self.session.commit()
            await self.session.refresh(instance)
            return instance
        except IntegrityError as e:
            await self.session.rollback()
            raise ResourceConflictError(f"Failed to create {self.model.__name__}", {"error": str(e)})
    
    async def get_by_id(self, id: Any) -> Optional[T]:
        """Get record by ID"""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_id_or_404(self, id: Any) -> T:
        """Get record by ID or raise 404 error"""
        instance = await self.get_by_id(id)
        if not instance:
            raise ResourceNotFoundError(self.model.__name__, str(id))
        return instance
    
    async def get_all(
        self, 
        offset: int = 0, 
        limit: int = 100,
        order_by: Optional[str] = None
    ) -> List[T]:
        """Get all records with pagination"""
        query = select(self.model)
        
        if order_by:
            if hasattr(self.model, order_by):
                query = query.order_by(getattr(self.model, order_by))
        
        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count(self) -> int:
        """Count total records"""
        result = await self.session.execute(
            select(func.count(self.model.id))
        )
        return result.scalar()
    
    async def update(self, id: Any, **kwargs) -> T:
        """Update record by ID"""
        instance = await self.get_by_id_or_404(id)
        
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        
        try:
            await self.session.commit()
            await self.session.refresh(instance)
            return instance
        except IntegrityError as e:
            await self.session.rollback()
            raise ResourceConflictError(f"Failed to update {self.model.__name__}", {"error": str(e)})
    
    async def delete(self, id: Any) -> bool:
        """Delete record by ID"""
        instance = await self.get_by_id_or_404(id)
        await self.session.delete(instance)
        await self.session.commit()
        return True
    
    async def find_by(self, **kwargs) -> List[T]:
        """Find records by attributes"""
        query = select(self.model)
        
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def find_one_by(self, **kwargs) -> Optional[T]:
        """Find one record by attributes"""
        results = await self.find_by(**kwargs)
        return results[0] if results else None
    
    async def exists(self, id: Any) -> bool:
        """Check if record exists"""
        result = await self.session.execute(
            select(func.count(self.model.id)).where(self.model.id == id)
        )
        return result.scalar() > 0


class DatabaseManager:
    """Database connection and transaction manager"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def execute_in_transaction(self, operation):
        """Execute operation in a transaction"""
        try:
            result = await operation(self.session)
            await self.session.commit()
            return result
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def bulk_create(self, model: Type[T], records: List[Dict[str, Any]]) -> List[T]:
        """Bulk create records"""
        try:
            instances = [model(**record) for record in records]
            self.session.add_all(instances)
            await self.session.commit()
            
            # Refresh all instances
            for instance in instances:
                await self.session.refresh(instance)
            
            return instances
        except IntegrityError as e:
            await self.session.rollback()
            raise ResourceConflictError(f"Failed to bulk create {model.__name__}", {"error": str(e)})
    
    async def bulk_update(self, model: Type[T], updates: List[Dict[str, Any]]) -> int:
        """Bulk update records"""
        try:
            updated_count = 0
            for update_data in updates:
                if 'id' not in update_data:
                    continue
                
                record_id = update_data.pop('id')
                result = await self.session.execute(
                    update(model).where(model.id == record_id).values(**update_data)
                )
                updated_count += result.rowcount
            
            await self.session.commit()
            return updated_count
        except IntegrityError as e:
            await self.session.rollback()
            raise ResourceConflictError(f"Failed to bulk update {model.__name__}", {"error": str(e)})
    
    async def raw_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute raw SQL query"""
        result = await self.session.execute(query, params or {})
        return [dict(row) for row in result.fetchall()]


async def with_transaction(session: AsyncSession, operation):
    """Helper function to execute operation in transaction"""
    db_manager = DatabaseManager(session)
    return await db_manager.execute_in_transaction(operation)


class DatabaseHealthCheck:
    """Database health check utility"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def check_connection(self) -> bool:
        """Check database connection"""
        try:
            await self.session.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    async def check_table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        try:
            result = await self.session.execute(
                f"SELECT 1 FROM information_schema.tables WHERE table_name = '{table_name}'"
            )
            return result.scalar() is not None
        except Exception:
            return False
    
    async def get_connection_info(self) -> Dict[str, Any]:
        """Get database connection information"""
        try:
            # Get database version
            result = await self.session.execute("SELECT version()")
            version = result.scalar()
            
            # Get current database name
            result = await self.session.execute("SELECT current_database()")
            database_name = result.scalar()
            
            return {
                "version": version,
                "database": database_name,
                "connection_status": "connected"
            }
        except Exception as e:
            return {
                "connection_status": "error",
                "error": str(e)
            }
