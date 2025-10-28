"""Logging utilities for telemetry and debugging"""
import logging
import time
import uuid
from functools import wraps
from typing import Callable, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


def setup_logging(debug: bool = False):
    """Configure logging"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware to add X-Request-ID header"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


def request_id_middleware(app: ASGIApp) -> ASGIApp:
    """Create request ID middleware"""
    return RequestIdMiddleware(app)


def log_timing(logger: logging.Logger, label: str):
    """
    Decorator to log execution time
    
    Usage:
        @log_timing(logger, "action_name")
        def my_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.time()
            try:
                result = func(*args, **kwargs)
                took_ms = int((time.time() - start) * 1000)
                logger.info(f"{label} completed in {took_ms}ms")
                return result
            except Exception as e:
                took_ms = int((time.time() - start) * 1000)
                logger.error(f"{label} failed after {took_ms}ms: {str(e)}")
                raise
        return wrapper
    return decorator

