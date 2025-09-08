"""
Circuit Breaker pattern implementation for external API calls
Prevents cascading failures when external services are down
"""

import time
import asyncio
from typing import Callable, Any, Optional, Dict
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5      # Failures before opening
    success_threshold: int = 2      # Successes to close from half-open
    timeout: int = 60              # Seconds to wait before half-open
    reset_timeout: int = 300       # Seconds before resetting counters
    
class CircuitBreakerException(Exception):
    """Raised when circuit breaker is open"""
    pass

class CircuitBreaker:
    """
    Circuit breaker implementation with failure tracking and automatic recovery
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_success_time = None
        self.next_attempt = 0
        
        # Statistics
        self.total_requests = 0
        self.total_failures = 0
        self.total_successes = 0
        self.total_rejected = 0
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker
        """
        self.total_requests += 1
        
        if not self._can_execute():
            self.total_rejected += 1
            raise CircuitBreakerException(
                f"Circuit breaker '{self.name}' is {self.state.value}. "
                f"Next retry in {max(0, self.next_attempt - time.time()):.0f} seconds"
            )
        
        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
            
        except Exception as e:
            self._record_failure()
            raise e
    
    def _can_execute(self) -> bool:
        """Check if request can be executed based on circuit state"""
        current_time = time.time()
        
        if self.state == CircuitState.CLOSED:
            return True
            
        elif self.state == CircuitState.OPEN:
            if current_time >= self.next_attempt:
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker '{self.name}' moving to HALF_OPEN state")
                return True
            return False
            
        elif self.state == CircuitState.HALF_OPEN:
            return True
            
        return False
    
    def _record_success(self):
        """Record successful execution"""
        self.total_successes += 1
        self.last_success_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._close_circuit()
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on successful execution
            self.failure_count = max(0, self.failure_count - 1)
    
    def _record_failure(self):
        """Record failed execution"""
        self.total_failures += 1
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self._open_circuit()
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self._open_circuit()
    
    def _open_circuit(self):
        """Open the circuit breaker"""
        self.state = CircuitState.OPEN
        self.success_count = 0
        self.next_attempt = time.time() + self.config.timeout
        logger.warning(
            f"Circuit breaker '{self.name}' opened due to {self.failure_count} failures. "
            f"Next attempt in {self.config.timeout} seconds"
        )
    
    def _close_circuit(self):
        """Close the circuit breaker"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        logger.info(f"Circuit breaker '{self.name}' closed after successful recovery")
    
    def reset(self):
        """Manually reset circuit breaker to closed state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.next_attempt = 0
        logger.info(f"Circuit breaker '{self.name}' manually reset")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        success_rate = (
            self.total_successes / max(1, self.total_requests) * 100
            if self.total_requests > 0 else 0
        )
        
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_requests": self.total_requests,
            "total_successes": self.total_successes,
            "total_failures": self.total_failures,
            "total_rejected": self.total_rejected,
            "success_rate": round(success_rate, 2),
            "last_failure_time": (
                datetime.fromtimestamp(self.last_failure_time).isoformat()
                if self.last_failure_time else None
            ),
            "last_success_time": (
                datetime.fromtimestamp(self.last_success_time).isoformat()
                if self.last_success_time else None
            ),
            "next_attempt": (
                datetime.fromtimestamp(self.next_attempt).isoformat()
                if self.next_attempt > time.time() else None
            )
        }

class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers"""
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
    
    def get_breaker(
        self, 
        name: str, 
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """Get or create a circuit breaker"""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name, config)
        return self._breakers[name]
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers"""
        return {name: breaker.get_stats() for name, breaker in self._breakers.items()}
    
    def reset_all(self):
        """Reset all circuit breakers"""
        for breaker in self._breakers.values():
            breaker.reset()
    
    def reset_breaker(self, name: str) -> bool:
        """Reset a specific circuit breaker"""
        if name in self._breakers:
            self._breakers[name].reset()
            return True
        return False

# Global registry instance
circuit_registry = CircuitBreakerRegistry()

def with_circuit_breaker(
    name: str, 
    config: Optional[CircuitBreakerConfig] = None
):
    """Decorator for applying circuit breaker to functions"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            breaker = circuit_registry.get_breaker(name, config)
            return await breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator

# Predefined configurations for common use cases
class CommonConfigs:
    # For external APIs that should fail fast
    EXTERNAL_API = CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout=30,
        reset_timeout=300
    )
    
    # For critical services that need more tolerance
    CRITICAL_SERVICE = CircuitBreakerConfig(
        failure_threshold=10,
        success_threshold=3,
        timeout=60,
        reset_timeout=600
    )
    
    # For optional services that can fail frequently
    OPTIONAL_SERVICE = CircuitBreakerConfig(
        failure_threshold=2,
        success_threshold=1,
        timeout=15,
        reset_timeout=120
    )