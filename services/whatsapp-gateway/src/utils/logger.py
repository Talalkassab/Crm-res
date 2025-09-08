import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
import uuid

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(JSONFormatter())
            self.logger.addHandler(handler)
    
    def _log(
        self,
        level: str,
        message: str,
        correlation_id: Optional[str] = None,
        **kwargs
    ):
        extra = {
            "correlation_id": correlation_id or str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        if level == "debug":
            self.logger.debug(message, extra={"structured": extra})
        elif level == "info":
            self.logger.info(message, extra={"structured": extra})
        elif level == "warning":
            self.logger.warning(message, extra={"structured": extra})
        elif level == "error":
            self.logger.error(message, extra={"structured": extra})
        elif level == "critical":
            self.logger.critical(message, extra={"structured": extra})
    
    def debug(self, message: str, correlation_id: Optional[str] = None, **kwargs):
        self._log("debug", message, correlation_id, **kwargs)
    
    def info(self, message: str, correlation_id: Optional[str] = None, **kwargs):
        self._log("info", message, correlation_id, **kwargs)
    
    def warning(self, message: str, correlation_id: Optional[str] = None, **kwargs):
        self._log("warning", message, correlation_id, **kwargs)
    
    def error(self, message: str, correlation_id: Optional[str] = None, **kwargs):
        self._log("error", message, correlation_id, **kwargs)
    
    def critical(self, message: str, correlation_id: Optional[str] = None, **kwargs):
        self._log("critical", message, correlation_id, **kwargs)
    
    def log_api_call(
        self,
        method: str,
        url: str,
        status_code: Optional[int] = None,
        duration_ms: Optional[float] = None,
        correlation_id: Optional[str] = None,
        error: Optional[str] = None
    ):
        self.info(
            f"API call: {method} {url}",
            correlation_id=correlation_id,
            method=method,
            url=url,
            status_code=status_code,
            duration_ms=duration_ms,
            error=error
        )
    
    def log_message_processing(
        self,
        message_id: str,
        from_number: str,
        message_type: str,
        status: str,
        correlation_id: Optional[str] = None,
        **kwargs
    ):
        self.info(
            f"Message processing: {message_id}",
            correlation_id=correlation_id,
            message_id=message_id,
            from_number=from_number,
            message_type=message_type,
            status=status,
            **kwargs
        )

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if hasattr(record, "structured"):
            log_data.update(record.structured)
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

def get_logger(name: str) -> StructuredLogger:
    return StructuredLogger(name)