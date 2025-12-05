"""
Structured logging configuration for CIS
Uses loguru for structured, rotated logs with trace IDs
"""
import sys
import uuid
from datetime import datetime
from pathlib import Path
from loguru import logger
from functools import wraps
import time

# Create logs directory
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Remove default handler
logger.remove()

# Console handler with color
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{extra[trace_id]}</cyan> | <level>{message}</level>",
    level="INFO",
    colorize=True,
    filter=lambda record: "trace_id" in record["extra"]
)

# File handler for all logs with rotation
logger.add(
    LOGS_DIR / "cis_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[trace_id]} | {message}",
    level="DEBUG",
    rotation="10 MB",
    retention="7 days",
    compression="zip",
    filter=lambda record: "trace_id" in record["extra"]
)

# Error-only file handler
logger.add(
    LOGS_DIR / "errors_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[trace_id]} | {message}\n{exception}",
    level="ERROR",
    rotation="5 MB",
    retention="30 days",
    compression="zip",
    filter=lambda record: "trace_id" in record["extra"]
)


def generate_trace_id() -> str:
    """Generate a unique trace ID for request tracking"""
    return f"cis-{uuid.uuid4().hex[:12]}"


def get_logger(trace_id: str = None):
    """Get a logger instance with trace ID context"""
    if trace_id is None:
        trace_id = generate_trace_id()
    return logger.bind(trace_id=trace_id)


def log_generation(
    trace_id: str,
    topic: str,
    score: int,
    duration_seconds: float,
    model: str,
    success: bool,
    user_id: str = None
):
    """Log a content generation event"""
    log = get_logger(trace_id)
    
    if success:
        log.info(
            f"GENERATION_SUCCESS | "
            f"topic='{topic[:50]}...' | "
            f"score={score} | "
            f"duration={duration_seconds:.2f}s | "
            f"model={model} | "
            f"user={user_id}"
        )
    else:
        log.error(
            f"GENERATION_FAILED | "
            f"topic='{topic[:50]}...' | "
            f"duration={duration_seconds:.2f}s | "
            f"model={model} | "
            f"user={user_id}"
        )


def log_error(trace_id: str, error: Exception, context: dict = None):
    """Log an error with full context"""
    log = get_logger(trace_id)
    context_str = " | ".join(f"{k}={v}" for k, v in (context or {}).items())
    log.exception(f"ERROR | {type(error).__name__}: {str(error)} | {context_str}")


def log_auth_event(event_type: str, user_id: str = None, email: str = None, success: bool = True):
    """Log authentication events"""
    log = get_logger(generate_trace_id())
    status = "SUCCESS" if success else "FAILED"
    log.info(f"AUTH_{event_type.upper()}_{status} | user_id={user_id} | email={email}")


def log_api_call(trace_id: str, api_name: str, duration_seconds: float, success: bool):
    """Log external API calls"""
    log = get_logger(trace_id)
    status = "SUCCESS" if success else "FAILED"
    log.info(f"API_CALL_{status} | api={api_name} | duration={duration_seconds:.2f}s")


def timed_operation(operation_name: str):
    """Decorator to log operation timing"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            trace_id = kwargs.get('trace_id', generate_trace_id())
            log = get_logger(trace_id)
            
            start = time.time()
            log.debug(f"OPERATION_START | {operation_name}")
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                log.info(f"OPERATION_SUCCESS | {operation_name} | duration={duration:.2f}s")
                return result
            except Exception as e:
                duration = time.time() - start
                log.error(f"OPERATION_FAILED | {operation_name} | duration={duration:.2f}s | error={str(e)}")
                raise
        
        return wrapper
    return decorator


# Initialize with a startup log
startup_log = get_logger(generate_trace_id())
startup_log.info("CIS Logging initialized")
