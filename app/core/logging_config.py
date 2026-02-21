"""
Structured logging configuration.
Spec reference: Implementation Plan Phase 4

This module configures:
- JSON formatter for production
- Human-readable formatter for development
- Log rotation (100MB per file, 10 backups)
- Separate loggers for app, sqlalchemy, uvicorn
"""

import logging
import logging.handlers
import json
from datetime import datetime
from pathlib import Path
from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for production.
    
    Outputs structured JSON logs with:
    - timestamp
    - level
    - logger name
    - message
    - correlation_id (if present)
    - additional context
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add correlation ID if present
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName",
                "relativeCreated", "thread", "threadName", "exc_info",
                "exc_text", "stack_info"
            ]:
                log_data[key] = value
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class HumanReadableFormatter(logging.Formatter):
    """
    Human-readable log formatter for development.
    
    Format: [timestamp] [level] [logger] message (correlation_id=...)
    """
    
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        base_msg = f"[{timestamp}] [{record.levelname}] [{record.name}] {record.getMessage()}"
        
        # Add correlation ID if present
        if hasattr(record, "correlation_id"):
            base_msg += f" (correlation_id={record.correlation_id})"
        
        # Add exception if present
        if record.exc_info:
            base_msg += "\n" + self.formatException(record.exc_info)
        
        return base_msg


def configure_logging():
    """
    Configure structured logging for the application.
    
    - Production: JSON formatter with file rotation
    - Development: Human-readable formatter to console
    """
    # Create logs directory if it doesn't exist
    log_file_path = Path(settings.LOG_FILE)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Select formatter based on environment
    if settings.ENV == "production":
        formatter = JSONFormatter()
    else:
        formatter = HumanReadableFormatter()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # File handler with rotation (100MB per file, 10 backups)
    file_handler = logging.handlers.RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=100 * 1024 * 1024,  # 100MB
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler (development only)
    if settings.ENV == "development":
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Configure SQLAlchemy logger (reduce verbosity)
    sqlalchemy_logger = logging.getLogger("sqlalchemy")
    sqlalchemy_logger.setLevel(logging.WARNING)
    
    # Configure uvicorn logger
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.setLevel(logging.INFO)
    
    logging.info(
        f"Logging configured: env={settings.ENV}, level={settings.LOG_LEVEL}, file={settings.LOG_FILE}"
    )


# Backward compatibility alias
setup_logging = configure_logging
