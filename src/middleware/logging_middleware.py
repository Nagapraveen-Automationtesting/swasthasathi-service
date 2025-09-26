"""
API Request/Response Logging Middleware for Swasthasathi Service
Provides comprehensive logging of all API interactions with context and performance metrics
"""
import time
import uuid
from datetime import datetime
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from src.config.logging_config import get_logger, log_api_request, log_api_response

# Get logger for this module
logger = get_logger(__name__)


class APILoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all API requests and responses with comprehensive context
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID for tracing
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Extract user context if available
        user_id = None
        try:
            # Try to extract user ID from authorization header
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # This is a simplified extraction - in practice you'd decode the JWT
                user_id = "authenticated_user"  # Placeholder
        except Exception:
            pass
        
        # Log incoming request
        log_api_request(
            method=request.method,
            endpoint=str(request.url.path),
            user_id=user_id,
            request_id=request_id
        )
        
        # Log detailed request info
        logger.info(f"API Request received", extra={
            'request_id': request_id,
            'method': request.method,
            'url': str(request.url),
            'path': request.url.path,
            'query_params': dict(request.query_params),
            'headers': dict(request.headers),
            'client_ip': request.client.host if request.client else None,
            'user_agent': request.headers.get('user-agent'),
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat() + "Z"
        })

        # Process request
        try:
            response = await call_next(request)
            
            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Log response
            log_api_response(
                method=request.method,
                endpoint=str(request.url.path),
                status_code=response.status_code,
                execution_time=execution_time,
                user_id=user_id,
                request_id=request_id
            )
            
            # Log detailed response info
            logger.info(f"API Response sent", extra={
                'request_id': request_id,
                'method': request.method,
                'endpoint': request.url.path,
                'status_code': response.status_code,
                'execution_time_ms': execution_time,
                'user_id': user_id,
                'response_headers': dict(response.headers) if hasattr(response, 'headers') else None,
                'timestamp': datetime.utcnow().isoformat() + "Z"
            })
            
            # Add request ID to response headers for tracing
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Execution-Time"] = str(execution_time)
            
            return response
            
        except Exception as e:
            # Calculate execution time for failed requests
            execution_time = (time.time() - start_time) * 1000
            
            # Log error response
            logger.error(f"API Request failed", extra={
                'request_id': request_id,
                'method': request.method,
                'endpoint': request.url.path,
                'error': str(e),
                'exception_type': type(e).__name__,
                'execution_time_ms': execution_time,
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat() + "Z"
            }, exc_info=True)
            
            # Re-raise the exception
            raise


class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log performance metrics and slow requests
    """

    def __init__(self, app: ASGIApp, slow_request_threshold: float = 1000.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold  # milliseconds

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        execution_time = (time.time() - start_time) * 1000
        
        # Log slow requests
        if execution_time > self.slow_request_threshold:
            logger.warning(f"Slow API request detected", extra={
                'method': request.method,
                'endpoint': request.url.path,
                'execution_time_ms': execution_time,
                'threshold_ms': self.slow_request_threshold,
                'status_code': response.status_code,
                'timestamp': datetime.utcnow().isoformat() + "Z"
            })
        
        # Log performance metrics
        logger.debug(f"Performance metrics", extra={
            'method': request.method,
            'endpoint': request.url.path,
            'execution_time_ms': execution_time,
            'status_code': response.status_code,
            'timestamp': datetime.utcnow().isoformat() + "Z"
        })
        
        return response


class HealthCheckLoggingFilter:
    """
    Filter to reduce noise from health check endpoints
    """
    
    @staticmethod
    def should_log_request(request: Request) -> bool:
        """
        Determine if a request should be logged based on the endpoint
        """
        # Skip logging health check endpoints to reduce noise
        health_endpoints = ["/health", "/healthz", "/ready", "/live"]
        
        for endpoint in health_endpoints:
            if request.url.path == endpoint:
                return False
        
        return True


class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log security-related events
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.security_logger = get_logger("security")

    async def dispatch(self, request: Request, call_next):
        # Log potential security events
        self._log_security_events(request)
        
        response = await call_next(request)
        
        # Log authentication failures
        if response.status_code == 401:
            self.security_logger.warning(f"Authentication failed", extra={
                'method': request.method,
                'endpoint': request.url.path,
                'client_ip': request.client.host if request.client else None,
                'user_agent': request.headers.get('user-agent'),
                'timestamp': datetime.utcnow().isoformat() + "Z"
            })
        
        # Log authorization failures
        elif response.status_code == 403:
            self.security_logger.warning(f"Authorization failed", extra={
                'method': request.method,
                'endpoint': request.url.path,
                'client_ip': request.client.host if request.client else None,
                'user_agent': request.headers.get('user-agent'),
                'timestamp': datetime.utcnow().isoformat() + "Z"
            })
        
        return response
    
    def _log_security_events(self, request: Request):
        """Log potential security events"""
        
        # Log requests with suspicious patterns
        suspicious_patterns = [
            '../', '..\\', '<script', 'javascript:', 'vbscript:',
            'onload=', 'onerror=', 'eval(', 'document.cookie',
            'union select', 'drop table', 'insert into'
        ]
        
        url_path = request.url.path.lower()
        query_string = str(request.url.query).lower()
        
        for pattern in suspicious_patterns:
            if pattern in url_path or pattern in query_string:
                self.security_logger.warning(f"Suspicious request pattern detected", extra={
                    'pattern': pattern,
                    'method': request.method,
                    'endpoint': request.url.path,
                    'query': str(request.url.query),
                    'client_ip': request.client.host if request.client else None,
                    'user_agent': request.headers.get('user-agent'),
                    'timestamp': datetime.utcnow().isoformat() + "Z"
                })
                break

