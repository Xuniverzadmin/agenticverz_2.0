"""
In-memory cache backend for BudgetLLM.

Simple, no dependencies, suitable for single-process usage.
"""

import hashlib
import json
import threading
import time
from typing import Any, Dict, Optional


class MemoryBackend:
    """
    Thread-safe in-memory cache backend.

    Features:
    - TTL support
    - LRU eviction at max capacity
    - Thread-safe operations

    Example:
        cache = MemoryBackend(max_size=1000, default_ttl=3600)
        cache.set("key", {"response": "hello"})
        value = cache.get("key")
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 3600,
    ):
        """
        Initialize memory cache.

        Args:
            max_size: Maximum number of entries
            default_ttl: Default TTL in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._store: Dict[str, Dict[str, Any]] = {}
        self._access_order: Dict[str, float] = {}
        self._lock = threading.Lock()

    def _generate_key(self, prompt_data: dict) -> str:
        """Generate cache key from prompt data."""
        normalized = json.dumps(prompt_data, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(normalized.encode()).hexdigest()

    def get(self, key: str) -> Optional[dict]:
        """
        Get cached value by key.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None

            # Check expiration
            if time.time() > entry["expires_at"]:
                del self._store[key]
                if key in self._access_order:
                    del self._access_order[key]
                return None

            # Update access time for LRU
            self._access_order[key] = time.time()
            return entry["value"]

    def set(
        self,
        key: str,
        value: dict,
        ttl: Optional[int] = None,
    ) -> None:
        """
        Store value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (uses default if not specified)
        """
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl

        with self._lock:
            # Evict if at capacity
            if len(self._store) >= self.max_size and key not in self._store:
                self._evict_oldest()

            self._store[key] = {
                "value": value,
                "expires_at": expires_at,
                "created_at": time.time(),
            }
            self._access_order[key] = time.time()

    def _evict_oldest(self) -> None:
        """Evict least recently accessed entry."""
        if not self._access_order:
            return

        oldest_key = min(self._access_order, key=self._access_order.get)
        if oldest_key in self._store:
            del self._store[oldest_key]
        if oldest_key in self._access_order:
            del self._access_order[oldest_key]

    def delete(self, key: str) -> bool:
        """
        Delete entry from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if key in self._store:
                del self._store[key]
                if key in self._access_order:
                    del self._access_order[key]
                return True
            return False

    def clear(self) -> int:
        """
        Clear all entries.

        Returns:
            Number of entries cleared
        """
        with self._lock:
            count = len(self._store)
            self._store.clear()
            self._access_order.clear()
            return count

    def size(self) -> int:
        """Get current number of entries."""
        return len(self._store)

    def stats(self) -> dict:
        """Get cache statistics."""
        with self._lock:
            return {
                "size": len(self._store),
                "max_size": self.max_size,
                "default_ttl": self.default_ttl,
            }
