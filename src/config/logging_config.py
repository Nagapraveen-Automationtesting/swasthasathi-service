"""
Comprehensive logging configuration for Swasthasathi Service
Provides structured, contextual logging with proper formatting and handlers
"""
import logging
import logging.handlers
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured logging with consistent format
    """
    
    def format(self, record: logging.LogRecord) -> str:
        # Create base log structure
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_data["user_id"] = record.user_id
        if hasattr(record, 'request_id'):
            log_data["request_id"] = record.request_id
        if hasattr(record, 'endpoint'):
            log_data["endpoint"] = record.endpoint
        if hasattr(record, 'method'):
            log_data["method"] = record.method
        if hasattr(record, 'status_code'):
            log_data["status_code"] = record.status_code
        if hasattr(record, 'execution_time'):
            log_data["execution_time_ms"] = record.execution_time
        
        return json.dumps(log_data, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """
    Human-readable console formatter for development
    """
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        # Add color if terminal supports it
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            reset = self.COLORS['RESET']
            record.levelname = f"{color}{record.levelname}{reset}"
        
        # Format: [TIMESTAMP] LEVEL [MODULE.FUNCTION:LINE] MESSAGE
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Add context if available
        context = ""
        if hasattr(record, 'user_id'):
            context += f" [user:{record.user_id}]"
        if hasattr(record, 'request_id'):
            context += f" [req:{record.request_id[:8]}]"
        
        base_msg = f"[{timestamp}] {record.levelname:<8} [{record.module}.{record.funcName}:{record.lineno}]{context} {record.getMessage()}"
        
        # Add exception if present
        if record.exc_info:
            base_msg += f"\n{self.formatException(record.exc_info)}"
        
        return base_msg


def setup_logging(
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_file_path: str = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    json_format: bool = False
) -> logging.Logger:
    """
    Setup comprehensive logging configuration for Swasthasathi Service
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file
        log_to_console: Whether to log to console
        log_file_path: Custom log file path
        max_file_size: Max size of log file before rotation
        backup_count: Number of backup files to keep
        json_format: Use JSON format for logs (recommended for production)
    
    Returns:
        Configured logger instance
    """
    
    # Create logs directory if it doesn't exist
    if log_to_file:
        if log_file_path is None:
            log_file_path = "logs/swasthasathi-service.log"
        
        log_dir = Path(log_file_path).parent
        log_dir.mkdir(exist_ok=True)
    
    # Get root logger
    logger = logging.getLogger("swasthasathi-service")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    # Console Handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        
        if json_format:
            console_handler.setFormatter(StructuredFormatter())
        else:
            console_handler.setFormatter(ConsoleFormatter())
        
        logger.addHandler(console_handler)
    
    # File Handler with rotation
    if log_to_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        
        # Always use structured format for file logs
        file_handler.setFormatter(StructuredFormatter())
        logger.addHandler(file_handler)
    
    # Error File Handler (separate file for errors)
    if log_to_file:
        error_file_path = log_file_path.replace('.log', '-errors.log')
        error_handler = logging.handlers.RotatingFileHandler(
            error_file_path,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter())
        logger.addHandler(error_handler)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance for a specific module
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance
    """
    if name is None:
        return logging.getLogger("swasthasathi-service")
    
    # Create hierarchical logger name
    if not name.startswith("swasthasathi-service"):
        name = f"swasthasathi-service.{name}"
    
    return logging.getLogger(name)


def log_function_call(func_name: str, args: Dict[str, Any] = None, user_id: str = None):
    """
    Decorator for logging function calls with context
    
    Args:
        func_name: Name of the function being called
        args: Function arguments to log
        user_id: User ID for context
    """
    logger = get_logger("function_calls")
    
    extra = {}
    if user_id:
        extra['user_id'] = user_id
    
    if args:
        logger.debug(f"Calling {func_name} with args: {args}", extra=extra)
    else:
        logger.debug(f"Calling {func_name}", extra=extra)


def log_api_request(method: str, endpoint: str, user_id: str = None, request_id: str = None):
    """
    Log API request details
    
    Args:
        method: HTTP method
        endpoint: API endpoint
        user_id: User ID for context
        request_id: Request ID for tracking
    """
    logger = get_logger("api_requests")
    
    extra = {
        'method': method,
        'endpoint': endpoint
    }
    
    if user_id:
        extra['user_id'] = user_id
    if request_id:
        extra['request_id'] = request_id
    
    logger.info(f"{method} {endpoint}", extra=extra)


def log_api_response(method: str, endpoint: str, status_code: int, execution_time: float = None, user_id: str = None, request_id: str = None):
    """
    Log API response details
    
    Args:
        method: HTTP method
        endpoint: API endpoint
        status_code: Response status code
        execution_time: Execution time in milliseconds
        user_id: User ID for context
        request_id: Request ID for tracking
    """
    logger = get_logger("api_responses")
    
    extra = {
        'method': method,
        'endpoint': endpoint,
        'status_code': status_code
    }
    
    if execution_time:
        extra['execution_time'] = execution_time
    if user_id:
        extra['user_id'] = user_id
    if request_id:
        extra['request_id'] = request_id
    
    if status_code >= 400:
        logger.error(f"{method} {endpoint} - {status_code}", extra=extra)
    else:
        logger.info(f"{method} {endpoint} - {status_code}", extra=extra)


def log_database_operation(operation: str, collection: str, query: Dict[str, Any] = None, result_count: int = None, execution_time: float = None):
    """
    Log database operations
    
    Args:
        operation: Database operation (find, insert, update, delete)
        collection: Collection name
        query: Query details (sanitized)
        result_count: Number of results
        execution_time: Execution time in milliseconds
    """
    logger = get_logger("database")
    
    extra = {
        'operation': operation,
        'collection': collection
    }
    
    if result_count is not None:
        extra['result_count'] = result_count
    if execution_time:
        extra['execution_time'] = execution_time
    
    message = f"Database {operation} on {collection}"
    if result_count is not None:
        message += f" - {result_count} results"
    
    logger.debug(message, extra=extra)


def log_security_event(event_type: str, user_id: str = None, ip_address: str = None, details: Dict[str, Any] = None):
    """
    Log security-related events
    
    Args:
        event_type: Type of security event (login_failed, unauthorized_access, etc.)
        user_id: User ID involved
        ip_address: IP address
        details: Additional details
    """
    logger = get_logger("security")
    
    extra = {
        'event_type': event_type
    }
    
    if user_id:
        extra['user_id'] = user_id
    if ip_address:
        extra['ip_address'] = ip_address
    if details:
        extra.update(details)
    
    logger.warning(f"Security event: {event_type}", extra=extra)


# Initialize default logger configuration
def init_logging():
    """Initialize logging with environment-based configuration"""
    
    # Get configuration from environment
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_to_file = os.getenv("LOG_TO_FILE", "true").lower() == "true"
    log_to_console = os.getenv("LOG_TO_CONSOLE", "true").lower() == "true"
    json_format = os.getenv("LOG_JSON_FORMAT", "false").lower() == "true"
    log_file_path = os.getenv("LOG_FILE_PATH", "logs/swasthasathi-service.log")
    
    # Setup logging
    return setup_logging(
        log_level=log_level,
        log_to_file=log_to_file,
        log_to_console=log_to_console,
        log_file_path=log_file_path,
        json_format=json_format
    )

