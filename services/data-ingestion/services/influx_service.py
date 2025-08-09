"""
InfluxDB Service for Data Ingestion Service
Handles writing IoT sensor data to InfluxDB
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict

from core.config import settings
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

logger = logging.getLogger(__name__)


class InfluxService:
    def __init__(self):
        self.client = None
        self.write_api = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize InfluxDB client"""
        try:
            print(f"Initializing InfluxDB client with URL: {settings.INFLUXDB_URL}")
            self.client = InfluxDBClient(
                url=settings.INFLUXDB_URL,
                token=settings.INFLUXDB_TOKEN,
                org=settings.INFLUXDB_ORG,
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            print("InfluxDB client initialized successfully")
            logger.info("InfluxDB client initialized successfully")
        except Exception as e:
            print(f"Error initializing InfluxDB client: {e}")
            logger.error(f"Error initializing InfluxDB client: {e}")

    async def write_energy_reading(
        self, device_id: str, data: Dict[str, Any], measurement: str = "energy_readings"
    ):
        """Write energy reading to InfluxDB"""
        try:
            print(f"Writing energy reading for device {device_id} to InfluxDB")
            # Create a point for the energy reading
            point = Point(measurement)
            
            # Add device_id as tag
            point = point.tag("device_id", device_id)
            
            # Add device type tag if available
            if "device_type" in data:
                point = point.tag("device_type", data["device_type"])
            
            # Add location tag if available
            if "location" in data:
                point = point.tag("location", data["location"])
                
            # Add zone tag if available
            if "zone" in data:
                point = point.tag("zone", data["zone"])
            
            # Add sensor fields
            if "power" in data and data["power"] is not None:
                point = point.field("power", float(data["power"]))
            
            if "energy" in data and data["energy"] is not None:
                point = point.field("energy", float(data["energy"]))
                
            if "voltage" in data and data["voltage"] is not None:
                point = point.field("voltage", float(data["voltage"]))
                
            if "current" in data and data["current"] is not None:
                point = point.field("current", float(data["current"]))
                
            if "temperature" in data and data["temperature"] is not None:
                point = point.field("temperature", float(data["temperature"]))
                
            if "efficiency" in data and data["efficiency"] is not None:
                point = point.field("efficiency", float(data["efficiency"]))
            
            # Use the timestamp from the data if available, otherwise use current time
            if "timestamp" in data:
                if isinstance(data["timestamp"], str):
                    # Parse ISO timestamp
                    timestamp = datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
                    point = point.time(timestamp)
                elif isinstance(data["timestamp"], datetime):
                    point = point.time(data["timestamp"])
            
            # Write to InfluxDB in a thread to avoid blocking
            if self.write_api:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    self.write_api.write,
                    settings.INFLUXDB_BUCKET,
                    settings.INFLUXDB_ORG,
                    point,
                )
                print(f"Successfully wrote energy reading for device {device_id} to InfluxDB")
                logger.debug(f"Wrote energy reading for device {device_id} to InfluxDB")
            else:
                print("InfluxDB write API not initialized")
                logger.error("InfluxDB write API not initialized")

        except Exception as e:
            print(f"Error writing energy reading to InfluxDB for device {device_id}: {e}")
            logger.error(f"Error writing energy reading to InfluxDB for device {device_id}: {e}")

    def close(self):
        """Close InfluxDB client connections"""
        if self.client:
            self.client.close()
            logger.info("InfluxDB client connections closed")


# Global InfluxDB service instance
influx_service = InfluxService()
