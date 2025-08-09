"""
Messaging utilities for inter-service communication
"""

import json
import asyncio
from typing import Dict, Any, Optional, Callable, List
from abc import ABC, abstractmethod


class MessageBroker(ABC):
    """Abstract base class for message brokers"""
    
    @abstractmethod
    async def publish(self, topic: str, message: Dict[str, Any]) -> bool:
        """Publish a message to a topic"""
        pass
    
    @abstractmethod
    async def subscribe(self, topic: str, callback: Callable) -> bool:
        """Subscribe to a topic with a callback function"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect from the broker"""
        pass


class InMemoryMessageBroker(MessageBroker):
    """In-memory message broker for development and testing"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.message_queue: List[Dict[str, Any]] = []
    
    async def publish(self, topic: str, message: Dict[str, Any]) -> bool:
        """Publish message to in-memory subscribers"""
        try:
            if topic in self.subscribers:
                for callback in self.subscribers[topic]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(message)
                        else:
                            callback(message)
                    except Exception as e:
                        print(f"Error in subscriber callback: {e}")
            
            # Store in queue for potential replay
            self.message_queue.append({
                "topic": topic,
                "message": message,
                "timestamp": asyncio.get_event_loop().time()
            })
            
            return True
        except Exception:
            return False
    
    async def subscribe(self, topic: str, callback: Callable) -> bool:
        """Subscribe to a topic"""
        try:
            if topic not in self.subscribers:
                self.subscribers[topic] = []
            self.subscribers[topic].append(callback)
            return True
        except Exception:
            return False
    
    async def disconnect(self):
        """Clear all subscriptions"""
        self.subscribers.clear()
        self.message_queue.clear()


class EventBus:
    """Simple event bus for application events"""
    
    def __init__(self):
        self.handlers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to an event type"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
    
    def unsubscribe(self, event_type: str, handler: Callable):
        """Unsubscribe from an event type"""
        if event_type in self.handlers:
            try:
                self.handlers[event_type].remove(handler)
            except ValueError:
                pass
    
    async def publish(self, event_type: str, data: Dict[str, Any]):
        """Publish an event"""
        if event_type in self.handlers:
            tasks = []
            for handler in self.handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        tasks.append(handler(data))
                    else:
                        handler(data)
                except Exception as e:
                    print(f"Error in event handler: {e}")
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)


class MessageQueue:
    """Simple message queue implementation"""
    
    def __init__(self, max_size: int = 1000):
        self.queue = asyncio.Queue(maxsize=max_size)
        self.processing = False
    
    async def put(self, message: Dict[str, Any]):
        """Add message to queue"""
        await self.queue.put(message)
    
    async def get(self) -> Dict[str, Any]:
        """Get message from queue"""
        return await self.queue.get()
    
    async def process_messages(self, processor: Callable):
        """Process messages with a given processor function"""
        self.processing = True
        try:
            while self.processing:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                    
                    if asyncio.iscoroutinefunction(processor):
                        await processor(message)
                    else:
                        processor(message)
                    
                    self.queue.task_done()
                    
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"Error processing message: {e}")
        except Exception as e:
            print(f"Error in message processing loop: {e}")
    
    def stop_processing(self):
        """Stop message processing"""
        self.processing = False
    
    def qsize(self) -> int:
        """Get queue size"""
        return self.queue.qsize()


class ServiceCommunication:
    """Utility for inter-service communication"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.event_bus = EventBus()
    
    async def send_event(self, target_service: str, event_type: str, data: Dict[str, Any]):
        """Send event to another service"""
        event_data = {
            "source_service": self.service_name,
            "target_service": target_service,
            "event_type": event_type,
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        await self.event_bus.publish(f"{target_service}.{event_type}", event_data)
    
    def subscribe_to_events(self, event_pattern: str, handler: Callable):
        """Subscribe to events from other services"""
        self.event_bus.subscribe(event_pattern, handler)
