"""
Device Simulator

Continuously simulates IoT device data streams
"""

import asyncio
import logging
from typing import Optional

from core.config import settings
from services.mock_device_manager import MockDeviceManager

logger = logging.getLogger(__name__)


class DeviceSimulator:
    """Simulates continuous data from IoT devices"""
    
    def __init__(self, device_manager: MockDeviceManager):
        self.device_manager = device_manager
        self.is_running = False
        self.simulation_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the device simulation"""
        if self.is_running:
            logger.warning("Device simulator is already running")
            return
        
        self.is_running = True
        self.simulation_task = asyncio.create_task(self._simulation_loop())
        logger.info("Device simulator started")
    
    async def stop(self):
        """Stop the device simulation"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.simulation_task:
            self.simulation_task.cancel()
            try:
                await self.simulation_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Device simulator stopped")
    
    async def _simulation_loop(self):
        """Main simulation loop"""
        try:
            while self.is_running:
                await self._simulate_all_devices()
                await asyncio.sleep(settings.SIMULATION_INTERVAL)
                
        except asyncio.CancelledError:
            logger.info("Simulation loop cancelled")
        except Exception as e:
            logger.error(f"Error in simulation loop: {e}")
    
    async def _simulate_all_devices(self):
        """Simulate data for all active devices"""
        try:
            devices = await self.device_manager.get_all_devices()
            
            # Publish data for each device concurrently
            tasks = []
            for device_id in devices.keys():
                task = asyncio.create_task(
                    self.device_manager.publish_device_data(device_id)
                )
                tasks.append(task)
            
            # Wait for all publications to complete
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Log any errors
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        device_id = list(devices.keys())[i]
                        logger.error(f"Error publishing data for {device_id}: {result}")
                
        except Exception as e:
            logger.error(f"Error simulating devices: {e}")
    
    async def simulate_device_once(self, device_id: str) -> bool:
        """Simulate data for a specific device once"""
        try:
            return await self.device_manager.publish_device_data(device_id)
        except Exception as e:
            logger.error(f"Error simulating device {device_id}: {e}")
            return False
