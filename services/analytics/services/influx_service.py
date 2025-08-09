import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from influxdb_client import InfluxDBClient
from influxdb_client.client.query_api import QueryApi

logger = logging.getLogger(__name__)


class InfluxService:
    def __init__(self, url: str, token: str, org: str, bucket: str):
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.client = None
        self.query_api = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize InfluxDB client"""
        try:
            self.client = InfluxDBClient(
                url=self.url,
                token=self.token,
                org=self.org
            )
            self.query_api = self.client.query_api()
            logger.info("InfluxDB client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing InfluxDB client: {e}")

    async def get_chart_data(
        self,
        field: str,  # "power" or "energy"
        interval: str,  # "minutely", "hourly", "daily"
        time_range: str,  # "1h", "24h", "7d", "30d"
        device_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get aggregated chart data from InfluxDB"""
        try:
            # Determine aggregation window based on interval
            aggregation_windows = {
                "minutely": "1m",
                "hourly": "1h", 
                "daily": "1d"
            }
            
            agg_window = aggregation_windows.get(interval, "1h")
            
            # Build query
            query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: -{time_range})
              |> filter(fn: (r) => r["_measurement"] == "energy_readings")
              |> filter(fn: (r) => r["_field"] == "{field}")
            '''
            
            # Filter by device if specified, otherwise aggregate across all devices
            if device_id:
                query += f' |> filter(fn: (r) => r["device_id"] == "{device_id}")'
            
            # Aggregate data with proper time alignment
            if interval == "minutely":
                # For minutely, use 1-minute windows
                query += f'''
              |> aggregateWindow(every: {agg_window}, fn: mean, createEmpty: false)
            '''
            elif interval == "hourly":
                # For hourly, group by hour and take mean - ensure we get one point per hour
                query += f'''
              |> aggregateWindow(every: {agg_window}, fn: mean, createEmpty: false, offset: 0s)
            '''
            else:  # daily
                # For daily, group by day and take mean
                query += f'''
              |> aggregateWindow(every: {agg_window}, fn: mean, createEmpty: false, offset: 0s)
            '''
            
            # If no specific device, aggregate across all devices for each time point
            if not device_id:
                query += f'''
              |> group(columns: ["_time", "_field", "_measurement"])
              |> mean()
            '''
            
            query += '''
              |> sort(columns: ["_time"])
              |> yield(name: "mean")
            '''
            
            logger.info(f"Executing InfluxDB query for {field} data: {query}")
            
            # Get event loop once
            loop = asyncio.get_event_loop()
            
            # First, let's check if there's any data in the bucket at all
            check_query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: -{time_range})
              |> filter(fn: (r) => r["_measurement"] == "energy_readings")
              |> limit(n: 5)
            '''
            
            logger.info(f"Checking for any data in bucket: {check_query}")
            check_result = await loop.run_in_executor(None, self.query_api.query, check_query)
            
            record_count = 0
            for table in check_result:
                for record in table.records:
                    record_count += 1
                    logger.info(f"Found record: time={record.get_time()}, field={record.get_field()}, value={record.get_value()}, device_id={record.values.get('device_id')}")
            
            logger.info(f"Total records found in check: {record_count}")

            # Execute query
            result = await loop.run_in_executor(None, self.query_api.query, query)

            # Convert result to chart data format
            data = []
            for table in result:
                for record in table.records:
                    timestamp = record.get_time()
                    value = record.get_value()
                    
                    # Format label based on interval
                    if interval == "minutely":
                        label = timestamp.strftime("%H:%M")
                    elif interval == "hourly":
                        label = timestamp.strftime("%H:00")
                    else:  # daily
                        label = timestamp.strftime("%b %d")
                    
                    data.append({
                        "timestamp": timestamp.isoformat(),
                        "value": round(value, 2) if value else 0,
                        "label": label
                    })

            logger.info(f"Retrieved {len(data)} {field} chart points for {time_range} range")
            return data

        except Exception as e:
            logger.error(f"Error getting chart data from InfluxDB: {e}")
            return []

    async def get_devices_with_data(self) -> List[str]:
        """Get list of devices that have data in InfluxDB"""
        try:
            query = f'''
            from(bucket: "{self.bucket}")
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
                    device_id = record.values.get("device_id")
                    if device_id and device_id not in devices:
                        devices.append(device_id)

            logger.info(f"Found {len(devices)} devices with data in InfluxDB")
            return devices

        except Exception as e:
            logger.error(f"Error getting devices from InfluxDB: {e}")
            return []

    def close(self):
        """Close InfluxDB client"""
        if self.client:
            self.client.close()
