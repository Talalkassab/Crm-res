import json
import asyncio
from typing import Any, Optional, Dict
from datetime import datetime, timedelta

class CacheManager:
    """Simple in-memory cache manager with TTL support."""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                
                # Check if entry has expired
                if entry["expires_at"] and datetime.now() > entry["expires_at"]:
                    del self._cache[key]
                    return None
                
                return entry["value"]
            
            return None
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        """Set value in cache with optional TTL in seconds."""
        async with self._lock:
            expires_at = None
            if expire:
                expires_at = datetime.now() + timedelta(seconds=expire)
            
            self._cache[key] = {
                "value": value,
                "expires_at": expires_at,
                "created_at": datetime.now()
            }
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
    
    async def cleanup_expired(self) -> int:
        """Remove expired entries from cache and return count removed."""
        removed_count = 0
        async with self._lock:
            now = datetime.now()
            expired_keys = []
            
            for key, entry in self._cache.items():
                if entry["expires_at"] and now > entry["expires_at"]:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                removed_count += 1
        
        return removed_count
    
    async def size(self) -> int:
        """Get current cache size."""
        async with self._lock:
            return len(self._cache)
    
    async def keys(self) -> list:
        """Get all cache keys."""
        async with self._lock:
            return list(self._cache.keys())

# Global cache instance
_global_cache = None

def get_cache_manager() -> CacheManager:
    """Get global cache manager instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = CacheManager()
    return _global_cache