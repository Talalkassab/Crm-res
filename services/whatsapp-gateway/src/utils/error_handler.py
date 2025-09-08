import asyncio
import logging
import random
import time
from typing import Optional, Callable, Any, Dict
from functools import wraps
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import uuid

logger = logging.getLogger(__name__)

class ErrorHandler:
    def __init__(
        self,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        max_attempts: int = 3,
        backoff_base: float = 2.0,
        jitter: bool = True
    ):
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.max_attempts = max_attempts
        self.backoff_base = backoff_base
        self.jitter = jitter
    
    def calculate_delay(self, attempt: int) -> float:
        delay = min(
            self.initial_delay * (self.backoff_base ** attempt),
            self.max_delay
        )
        
        if self.jitter:
            delay = delay * (0.5 + random.random())
        
        return delay
    
    async def retry_with_backoff(
        self,
        func: Callable,
        *args,
        correlation_id: Optional[str] = None,
        **kwargs
    ) -> Any:
        correlation_id = correlation_id or str(uuid.uuid4())
        
        for attempt in range(self.max_attempts):
            try:
                logger.info(f"[{correlation_id}] Attempt {attempt + 1}/{self.max_attempts} for {func.__name__}")
                result = await func(*args, **kwargs)
                
                if attempt > 0:
                    logger.info(f"[{correlation_id}] Success after {attempt + 1} attempts")
                
                return result
                
            except Exception as e:
                if attempt == self.max_attempts - 1:
                    logger.error(
                        f"[{correlation_id}] Max attempts reached for {func.__name__}: {str(e)}"
                    )
                    raise
                
                delay = self.calculate_delay(attempt)
                logger.warning(
                    f"[{correlation_id}] Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                    f"Retrying in {delay:.2f}s..."
                )
                
                await asyncio.sleep(delay)
    
    def sync_retry_with_backoff(self, func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            correlation_id = str(uuid.uuid4())
            
            for attempt in range(self.max_attempts):
                try:
                    logger.info(f"[{correlation_id}] Attempt {attempt + 1}/{self.max_attempts} for {func.__name__}")
                    result = func(*args, **kwargs)
                    
                    if attempt > 0:
                        logger.info(f"[{correlation_id}] Success after {attempt + 1} attempts")
                    
                    return result
                    
                except Exception as e:
                    if attempt == self.max_attempts - 1:
                        logger.error(
                            f"[{correlation_id}] Max attempts reached for {func.__name__}: {str(e)}"
                        )
                        raise
                    
                    delay = self.calculate_delay(attempt)
                    logger.warning(
                        f"[{correlation_id}] Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    time.sleep(delay)
        
        return wrapper

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == "OPEN":
            if self.last_failure_time and \
               (time.time() - self.last_failure_time) > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info(f"Circuit breaker entering HALF_OPEN state for {func.__name__}")
            else:
                raise Exception(f"Circuit breaker is OPEN for {func.__name__}")
        
        try:
            result = await func(*args, **kwargs)
            
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                logger.info(f"Circuit breaker CLOSED for {func.__name__}")
            
            return result
            
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.error(
                    f"Circuit breaker OPEN for {func.__name__} after {self.failure_count} failures"
                )
            
            raise

def create_error_response(
    status_code: int,
    message: str,
    correlation_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": message,
            "correlation_id": correlation_id or str(uuid.uuid4()),
            "details": details or {}
        }
    )

async def global_exception_handler(request: Request, exc: Exception):
    correlation_id = str(uuid.uuid4())
    
    if isinstance(exc, HTTPException):
        logger.warning(f"[{correlation_id}] HTTP exception: {exc.detail}")
        return create_error_response(
            status_code=exc.status_code,
            message=exc.detail,
            correlation_id=correlation_id
        )
    
    logger.error(f"[{correlation_id}] Unhandled exception: {str(exc)}", exc_info=True)
    
    return create_error_response(
        status_code=500,
        message="Internal server error",
        correlation_id=correlation_id,
        details={"error_type": type(exc).__name__}
    )

error_handler = ErrorHandler()
webhook_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60.0,
    expected_exception=Exception
)