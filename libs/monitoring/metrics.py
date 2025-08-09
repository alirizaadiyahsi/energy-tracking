"""
Metrics collection and monitoring utilities
"""

import time
import threading
import asyncio
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from datetime import datetime, timedelta


@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: float
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricSummary:
    """Metric summary statistics"""
    count: int
    sum: float
    min: float
    max: float
    avg: float
    p50: float
    p95: float
    p99: float


class MetricsRegistry:
    """Registry for collecting and managing metrics"""
    
    def __init__(self, max_points_per_metric: int = 1000):
        self.max_points = max_points_per_metric
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=self.max_points))
        self.timers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=self.max_points))
        self._lock = threading.Lock()
    
    def increment_counter(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        key = self._make_key(name, tags)
        with self._lock:
            self.counters[key] += value
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric"""
        key = self._make_key(name, tags)
        with self._lock:
            self.gauges[key] = value
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a histogram value"""
        key = self._make_key(name, tags)
        point = MetricPoint(timestamp=time.time(), value=value, tags=tags or {})
        with self._lock:
            self.histograms[key].append(point)
    
    def record_timer(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None):
        """Record a timer duration"""
        key = self._make_key(name, tags)
        point = MetricPoint(timestamp=time.time(), value=duration, tags=tags or {})
        with self._lock:
            self.timers[key].append(point)
    
    def get_counter(self, name: str, tags: Optional[Dict[str, str]] = None) -> float:
        """Get counter value"""
        key = self._make_key(name, tags)
        return self.counters.get(key, 0.0)
    
    def get_gauge(self, name: str, tags: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get gauge value"""
        key = self._make_key(name, tags)
        return self.gauges.get(key)
    
    def get_histogram_summary(self, name: str, tags: Optional[Dict[str, str]] = None) -> Optional[MetricSummary]:
        """Get histogram summary statistics"""
        key = self._make_key(name, tags)
        points = list(self.histograms.get(key, []))
        
        if not points:
            return None
        
        values = [p.value for p in points]
        values.sort()
        
        count = len(values)
        total = sum(values)
        
        return MetricSummary(
            count=count,
            sum=total,
            min=values[0],
            max=values[-1],
            avg=total / count,
            p50=values[int(count * 0.5)] if count > 0 else 0,
            p95=values[int(count * 0.95)] if count > 0 else 0,
            p99=values[int(count * 0.99)] if count > 0 else 0
        )
    
    def get_timer_summary(self, name: str, tags: Optional[Dict[str, str]] = None) -> Optional[MetricSummary]:
        """Get timer summary statistics"""
        key = self._make_key(name, tags)
        points = list(self.timers.get(key, []))
        
        if not points:
            return None
        
        values = [p.value for p in points]
        values.sort()
        
        count = len(values)
        total = sum(values)
        
        return MetricSummary(
            count=count,
            sum=total,
            min=values[0],
            max=values[-1],
            avg=total / count,
            p50=values[int(count * 0.5)] if count > 0 else 0,
            p95=values[int(count * 0.95)] if count > 0 else 0,
            p99=values[int(count * 0.99)] if count > 0 else 0
        )
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        with self._lock:
            return {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {k: [{"timestamp": p.timestamp, "value": p.value, "tags": p.tags} 
                                 for p in v] for k, v in self.histograms.items()},
                "timers": {k: [{"timestamp": p.timestamp, "value": p.value, "tags": p.tags} 
                             for p in v] for k, v in self.timers.items()}
            }
    
    def reset(self):
        """Reset all metrics"""
        with self._lock:
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()
            self.timers.clear()
    
    def _make_key(self, name: str, tags: Optional[Dict[str, str]]) -> str:
        """Create metric key with tags"""
        if not tags:
            return name
        
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"


class Timer:
    """Context manager for timing operations"""
    
    def __init__(self, registry: MetricsRegistry, name: str, tags: Optional[Dict[str, str]] = None):
        self.registry = registry
        self.name = name
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.registry.record_timer(self.name, duration, self.tags)


def timer_decorator(registry: MetricsRegistry, name: Optional[str] = None, tags: Optional[Dict[str, str]] = None):
    """Decorator for timing function execution"""
    def decorator(func: Callable):
        metric_name = name or f"{func.__module__}.{func.__name__}"
        
        def sync_wrapper(*args, **kwargs):
            with Timer(registry, metric_name, tags):
                return func(*args, **kwargs)
        
        async def async_wrapper(*args, **kwargs):
            with Timer(registry, metric_name, tags):
                return await func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class PerformanceMonitor:
    """Monitor system and application performance"""
    
    def __init__(self, registry: MetricsRegistry):
        self.registry = registry
        self.monitoring = False
        self._monitor_task = None
    
    async def start_monitoring(self, interval: float = 30.0):
        """Start performance monitoring"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop(interval))
    
    async def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
    
    async def _monitoring_loop(self, interval: float):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval)
    
    async def _collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            import psutil
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.registry.set_gauge("system.cpu.percent", cpu_percent)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.registry.set_gauge("system.memory.percent", memory.percent)
            self.registry.set_gauge("system.memory.available", memory.available)
            self.registry.set_gauge("system.memory.used", memory.used)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            self.registry.set_gauge("system.disk.percent", (disk.used / disk.total) * 100)
            self.registry.set_gauge("system.disk.free", disk.free)
            self.registry.set_gauge("system.disk.used", disk.used)
            
            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            self.registry.set_gauge("process.memory.rss", process_memory.rss)
            self.registry.set_gauge("process.memory.vms", process_memory.vms)
            self.registry.set_gauge("process.cpu.percent", process.cpu_percent())
            
        except ImportError:
            # psutil not available
            pass
        except Exception as e:
            print(f"Error collecting system metrics: {e}")


# Global metrics registry
metrics_registry = MetricsRegistry()


def get_metrics_registry() -> MetricsRegistry:
    """Get the global metrics registry"""
    return metrics_registry


def increment_counter(name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
    """Increment a counter in the global registry"""
    metrics_registry.increment_counter(name, value, tags)


def set_gauge(name: str, value: float, tags: Optional[Dict[str, str]] = None):
    """Set a gauge in the global registry"""
    metrics_registry.set_gauge(name, value, tags)


def record_histogram(name: str, value: float, tags: Optional[Dict[str, str]] = None):
    """Record a histogram value in the global registry"""
    metrics_registry.record_histogram(name, value, tags)


def record_timer(name: str, duration: float, tags: Optional[Dict[str, str]] = None):
    """Record a timer duration in the global registry"""
    metrics_registry.record_timer(name, duration, tags)


def time_it(name: Optional[str] = None, tags: Optional[Dict[str, str]] = None):
    """Decorator for timing functions"""
    return timer_decorator(metrics_registry, name, tags)


class MetricsCollector:
    """Service-specific metrics collector"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.registry = get_metrics_registry()
    
    def increment_counter(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        full_name = f"{self.service_name}.{name}"
        service_tags = {"service": self.service_name}
        if tags:
            service_tags.update(tags)
        self.registry.increment_counter(full_name, value, service_tags)
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric"""
        full_name = f"{self.service_name}.{name}"
        service_tags = {"service": self.service_name}
        if tags:
            service_tags.update(tags)
        self.registry.set_gauge(full_name, value, service_tags)
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a histogram value"""
        full_name = f"{self.service_name}.{name}"
        service_tags = {"service": self.service_name}
        if tags:
            service_tags.update(tags)
        self.registry.record_histogram(full_name, value, service_tags)
    
    def record_timer(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None):
        """Record a timer duration"""
        full_name = f"{self.service_name}.{name}"
        service_tags = {"service": self.service_name}
        if tags:
            service_tags.update(tags)
        self.registry.record_timer(full_name, duration, service_tags)
    
    def time_operation(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Context manager for timing operations"""
        full_name = f"{self.service_name}.{name}"
        service_tags = {"service": self.service_name}
        if tags:
            service_tags.update(tags)
        
        class TimerContext:
            def __init__(self, registry, metric_name, metric_tags):
                self.registry = registry
                self.metric_name = metric_name
                self.metric_tags = metric_tags
                self.start_time = None
            
            def __enter__(self):
                self.start_time = time.time()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                duration = time.time() - self.start_time
                self.registry.record_timer(self.metric_name, duration, self.metric_tags)
        
        return TimerContext(self.registry, full_name, service_tags)


def setup_metrics_endpoint(app, registry: Optional[MetricsRegistry] = None):
    """Setup metrics endpoint for FastAPI application"""
    if registry is None:
        registry = MetricsRegistry()
    
    @app.get("/metrics")
    async def get_metrics():
        """Get metrics in Prometheus format"""
        lines = []
        
        # Add counters
        for name, value in registry.counters.items():
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")
        
        # Add gauges
        for name, value in registry.gauges.items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")
        
        return "\n".join(lines)
    
    return registry
