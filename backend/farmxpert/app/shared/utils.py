"""
Shared Utilities for FarmXpert Platform
Common helper functions used across all agents
"""

import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from farmxpert.app.config import settings


def setup_logging():
    """Setup application logging configuration"""
    
    # Configure logging format
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s"
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format=log_format,
        stream=sys.stdout,
        force=True
    )
    
    # Create logger for the application
    logger = logging.getLogger("farmxpert")
    
    # Add file logging if specified
    if settings.log_file:
        log_path = Path(settings.log_file)
        if log_path.parent:
            log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(log_path))
        file_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(file_handler)
    
    return logger


def get_current_utc_time() -> datetime:
    """Get current UTC time"""
    return datetime.now(timezone.utc)


def format_timestamp(dt: datetime) -> str:
    """Format datetime to ISO 8601 string"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get value from dictionary with nested key support"""
    keys = key.split('.')
    current = data
    
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return default
    
    return current


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries recursively"""
    result = {}
    
    for d in dicts:
        for key, value in d.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_dicts(result[key], value)
            else:
                result[key] = value
    
    return result


def validate_coordinates(latitude: float, longitude: float) -> bool:
    """Validate geographic coordinates"""
    return -90 <= latitude <= 90 and -180 <= longitude <= 180


def calculate_days_between(start_date: datetime, end_date: datetime) -> int:
    """Calculate days between two dates"""
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)
    
    delta = end_date - start_date
    return abs(delta.days)


def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """Sanitize string input"""
    if not text:
        return ""
    
    # Remove extra whitespace
    sanitized = ' '.join(text.split())
    
    # Truncate if max_length is specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip()
    
    return sanitized


def create_error_response(
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create standardized error response"""
    response = {
        "error": True,
        "error_code": error_code,
        "message": message,
        "timestamp": format_timestamp(get_current_utc_time())
    }
    
    if details:
        response["details"] = details
    
    return response


def create_success_response(
    data: Any,
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create standardized success response"""
    response = {
        "success": True,
        "data": data,
        "timestamp": format_timestamp(get_current_utc_time())
    }
    
    if message:
        response["message"] = message
    
    if metadata:
        response["metadata"] = metadata
    
    return response


def list_files_in_directory(directory: Path, pattern: str = "*") -> List[Path]:
    """List files in directory with optional pattern matching"""
    if not directory.exists() or not directory.is_dir():
        return []
    
    return list(directory.glob(pattern))


def ensure_directory_exists(directory: Path) -> Path:
    """Ensure directory exists, create if it doesn't"""
    directory.mkdir(parents=True, exist_ok=True)
    return directory


# Initialize logger
logger = setup_logging()
