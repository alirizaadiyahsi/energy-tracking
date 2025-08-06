import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import asyncio

from core.config import settings

logger = logging.getLogger(__name__)

class InfluxService:
    def __init__(self):
        self.client = None
        self.write_api = None
        self.query_api = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize InfluxDB client"""
        try:
            self.client = InfluxDBClient(
                url=settings.INFLUXDB_URL,
                token=settings.INFLUXDB_TOKEN,
                org=settings.INFLUXDB_ORG
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()
            logger.info("InfluxDB client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing InfluxDB client: {e}")
    
    async def get_energy_data(
        self, 
        device_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        measurement: str = "energy_readings"
    ) -> List[Dict[str, Any]]:
        """Get energy data from InfluxDB"""
        try:
            # Build query
            query = f'from(bucket: "{settings.INFLUXDB_BUCKET}")'
            
            # Time range
            if start_time:
                query += f' |> range(start: {start_time.isoformat()}Z'
                if end_time:
                    query += f', stop: {end_time.isoformat()}Z'
                query += ')'
            else:
                query += ' |> range(start: -24h)'
            
            # Filter by measurement
            query += f' |> filter(fn: (r) => r["_measurement"] == "{measurement}")'
            
            # Filter by device if specified
            if device_id:
                query += f' |> filter(fn: (r) => r["device_id"] == "{device_id}")'
            
            # Sort by time
            query += ' |> sort(columns: ["_time"], desc: false)'
            
            # Execute query in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.query_api.query, query)
            
            # Convert result to list of dictionaries
            data = []
            for table in result:
                for record in table.records:
                    data.append({
                        'timestamp': record.get_time(),
                        'device_id': record.values.get('device_id'),
                        'measurement': record.get_measurement(),
                        'field': record.get_field(),
                        'value': record.get_value(),
                        'power': record.values.get('power', 0.0),
                        'energy': record.values.get('energy', 0.0),
                        'voltage': record.values.get('voltage', 0.0),
                        'current': record.values.get('current', 0.0)
                    })
            
            logger.info(f"Retrieved {len(data)} records from InfluxDB")
            return data
            
        except Exception as e:
            logger.error(f"Error getting energy data from InfluxDB: {e}")
            return []
    
    async def write_processed_data(self, data: List[Dict[str, Any]], measurement: str = "processed_metrics"):
        """Write processed data back to InfluxDB"""
        try:
            points = []
            
            for record in data:
                point = Point(measurement)
                
                # Add tags
                if 'device_id' in record:
                    point = point.tag("device_id", record['device_id'])
                if 'metric_type' in record:
                    point = point.tag("metric_type", record['metric_type'])
                
                # Add fields
                for key, value in record.items():
                    if key not in ['device_id', 'metric_type', 'timestamp'] and value is not None:
                        if isinstance(value, (int, float)):
                            point = point.field(key, value)
                
                # Set timestamp
                if 'timestamp' in record:
                    point = point.time(record['timestamp'])
                
                points.append(point)
            
            if points:
                # Write in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None, 
                    self.write_api.write,
                    settings.INFLUXDB_BUCKET,
                    settings.INFLUXDB_ORG,
                    points
                )
                logger.info(f"Wrote {len(points)} processed data points to InfluxDB")
        
        except Exception as e:
            logger.error(f"Error writing processed data to InfluxDB: {e}")
    
    async def get_device_list(self) -> List[str]:
        """Get list of unique device IDs from InfluxDB"""
        try:
            query = f'''
            from(bucket: "{settings.INFLUXDB_BUCKET}")
              |> range(start: -30d)
              |> filter(fn: (r) => r["_measurement"] == "energy_readings")
              |> group(columns: ["device_id"])
              |> distinct(column: "device_id")
              |> keep(columns: ["device_id"])
            '''
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.query_api.query, query)
            
            devices = []
            for table in result:
                for record in table.records:
                    device_id = record.values.get('device_id')
                    if device_id and device_id not in devices:
                        devices.append(device_id)
            
            logger.info(f"Found {len(devices)} unique devices in InfluxDB")
            return devices
            
        except Exception as e:
            logger.error(f"Error getting device list from InfluxDB: {e}")
            return []
    
    async def get_aggregated_data(
        self,
        device_id: Optional[str] = None,
        aggregation_window: str = "1h",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get pre-aggregated data from InfluxDB"""
        try:
            # Build query
            query = f'from(bucket: "{settings.INFLUXDB_BUCKET}")'
            
            # Time range
            if start_time:
                query += f' |> range(start: {start_time.isoformat()}Z'
                if end_time:
                    query += f', stop: {end_time.isoformat()}Z'
                query += ')'
            else:
                query += ' |> range(start: -7d)'
            
            # Filter by measurement
            query += ' |> filter(fn: (r) => r["_measurement"] == "energy_readings")'
            
            # Filter by device if specified
            if device_id:
                query += f' |> filter(fn: (r) => r["device_id"] == "{device_id}")'
            
            # Aggregate by time window
            query += f'''
              |> aggregateWindow(every: {aggregation_window}, fn: mean, createEmpty: false)
              |> yield(name: "mean")
            '''
            
            # Execute query
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.query_api.query, query)
            
            # Convert result to list of dictionaries
            data = []
            for table in result:
                for record in table.records:
                    data.append({
                        'timestamp': record.get_time(),
                        'device_id': record.values.get('device_id'),
                        'field': record.get_field(),
                        'value': record.get_value()
                    })
            
            logger.info(f"Retrieved {len(data)} aggregated records from InfluxDB")
            return data
            
        except Exception as e:
            logger.error(f"Error getting aggregated data from InfluxDB: {e}")
            return []
    
    def close(self):
        """Close InfluxDB client connections"""
        if self.client:
            self.client.close()
            logger.info("InfluxDB client connections closed")
