"""
Distributed tracing utilities
"""

import time
import uuid
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from contextvars import ContextVar
from datetime import datetime


# Context variables for tracing
trace_context: ContextVar[Optional['TraceContext']] = ContextVar('trace_context', default=None)


@dataclass
class Span:
    """Represents a single span in a trace"""
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "ok"  # ok, error, timeout
    
    @property
    def duration(self) -> Optional[float]:
        """Get span duration in seconds"""
        if self.end_time:
            return self.end_time - self.start_time
        return None
    
    def finish(self, status: str = "ok"):
        """Finish the span"""
        self.end_time = time.time()
        self.status = status
    
    def set_tag(self, key: str, value: Any):
        """Set a tag on the span"""
        self.tags[key] = value
    
    def log(self, message: str, level: str = "info", **kwargs):
        """Add a log entry to the span"""
        self.logs.append({
            "timestamp": time.time(),
            "level": level,
            "message": message,
            **kwargs
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary"""
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "operation_name": self.operation_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "tags": self.tags,
            "logs": self.logs,
            "status": self.status
        }


@dataclass
class TraceContext:
    """Trace context containing current trace information"""
    trace_id: str
    current_span: Optional[Span] = None
    spans: List[Span] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trace context to dictionary"""
        return {
            "trace_id": self.trace_id,
            "spans": [span.to_dict() for span in self.spans]
        }


class Tracer:
    """Distributed tracer for creating and managing spans"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self._traces: Dict[str, TraceContext] = {}
        self._lock = threading.Lock()
    
    def start_trace(self, operation_name: str, trace_id: Optional[str] = None) -> TraceContext:
        """Start a new trace"""
        if not trace_id:
            trace_id = str(uuid.uuid4())
        
        context = TraceContext(trace_id=trace_id)
        span = self.start_span(operation_name, context=context)
        
        with self._lock:
            self._traces[trace_id] = context
        
        trace_context.set(context)
        return context
    
    def start_span(
        self, 
        operation_name: str, 
        parent_span: Optional[Span] = None,
        context: Optional[TraceContext] = None
    ) -> Span:
        """Start a new span"""
        if not context:
            context = trace_context.get()
            if not context:
                # Start new trace if no context
                context = self.start_trace(operation_name)
                return context.current_span
        
        span_id = str(uuid.uuid4())
        parent_span_id = parent_span.span_id if parent_span else (
            context.current_span.span_id if context.current_span else None
        )
        
        span = Span(
            span_id=span_id,
            trace_id=context.trace_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            start_time=time.time()
        )
        
        # Add service tag
        span.set_tag("service.name", self.service_name)
        
        context.spans.append(span)
        context.current_span = span
        
        return span
    
    def finish_span(self, span: Span, status: str = "ok"):
        """Finish a span"""
        span.finish(status)
        
        context = trace_context.get()
        if context and context.current_span == span:
            # Find parent span to set as current
            parent_span = None
            if span.parent_span_id:
                for s in context.spans:
                    if s.span_id == span.parent_span_id:
                        parent_span = s
                        break
            context.current_span = parent_span
    
    def get_trace(self, trace_id: str) -> Optional[TraceContext]:
        """Get trace by ID"""
        with self._lock:
            return self._traces.get(trace_id)
    
    def get_all_traces(self) -> List[TraceContext]:
        """Get all traces"""
        with self._lock:
            return list(self._traces.values())
    
    def clear_old_traces(self, max_age_seconds: float = 3600):
        """Clear traces older than max_age_seconds"""
        cutoff_time = time.time() - max_age_seconds
        
        with self._lock:
            to_remove = []
            for trace_id, context in self._traces.items():
                # Check if any span in the trace is newer than cutoff
                if all(span.start_time < cutoff_time for span in context.spans):
                    to_remove.append(trace_id)
            
            for trace_id in to_remove:
                del self._traces[trace_id]


class SpanContext:
    """Context manager for spans"""
    
    def __init__(self, tracer: Tracer, operation_name: str):
        self.tracer = tracer
        self.operation_name = operation_name
        self.span = None
    
    def __enter__(self) -> Span:
        self.span = self.tracer.start_span(self.operation_name)
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            status = "error" if exc_type else "ok"
            if exc_type:
                self.span.log(f"Exception: {exc_val}", level="error", exception_type=str(exc_type))
            self.tracer.finish_span(self.span, status)


def trace_decorator(tracer: Tracer, operation_name: Optional[str] = None):
    """Decorator for tracing functions"""
    def decorator(func):
        name = operation_name or f"{func.__module__}.{func.__name__}"
        
        def sync_wrapper(*args, **kwargs):
            with SpanContext(tracer, name) as span:
                span.set_tag("function.name", func.__name__)
                span.set_tag("function.module", func.__module__)
                return func(*args, **kwargs)
        
        async def async_wrapper(*args, **kwargs):
            with SpanContext(tracer, name) as span:
                span.set_tag("function.name", func.__name__)
                span.set_tag("function.module", func.__module__)
                return await func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class TraceExporter:
    """Export traces to external systems"""
    
    def __init__(self, tracer: Tracer):
        self.tracer = tracer
    
    def export_to_jaeger(self, jaeger_endpoint: str):
        """Export traces to Jaeger (placeholder implementation)"""
        # This would implement actual Jaeger export
        traces = self.tracer.get_all_traces()
        print(f"Would export {len(traces)} traces to Jaeger at {jaeger_endpoint}")
    
    def export_to_zipkin(self, zipkin_endpoint: str):
        """Export traces to Zipkin (placeholder implementation)"""
        # This would implement actual Zipkin export
        traces = self.tracer.get_all_traces()
        print(f"Would export {len(traces)} traces to Zipkin at {zipkin_endpoint}")
    
    def export_to_json(self, file_path: str):
        """Export traces to JSON file"""
        import json
        traces = self.tracer.get_all_traces()
        trace_data = [trace.to_dict() for trace in traces]
        
        with open(file_path, 'w') as f:
            json.dump(trace_data, f, indent=2, default=str)


# Global tracer instance
_global_tracer: Optional[Tracer] = None


def get_tracer(service_name: Optional[str] = None) -> Tracer:
    """Get or create global tracer"""
    global _global_tracer
    if not _global_tracer:
        if not service_name:
            service_name = "unknown-service"
        _global_tracer = Tracer(service_name)
    return _global_tracer


def start_span(operation_name: str) -> Span:
    """Start a span using the global tracer"""
    tracer = get_tracer()
    return tracer.start_span(operation_name)


def trace(operation_name: Optional[str] = None):
    """Decorator for tracing using the global tracer"""
    tracer = get_tracer()
    return trace_decorator(tracer, operation_name)


def setup_tracing(app, service_name: str):
    """Setup tracing for FastAPI application"""
    global _global_tracer
    _global_tracer = Tracer(service_name)
    
    @app.middleware("http")
    async def tracing_middleware(request, call_next):
        """Add tracing to HTTP requests"""
        span = _global_tracer.start_span(f"{request.method} {request.url.path}")
        span.set_tag("http.method", request.method)
        span.set_tag("http.url", str(request.url))
        
        try:
            response = await call_next(request)
            span.set_tag("http.status_code", response.status_code)
            span.finish("ok")
            return response
        except Exception as e:
            span.set_tag("error", True)
            span.log(f"Error: {str(e)}", level="error")
            span.finish("error")
            raise
    
    return _global_tracer
