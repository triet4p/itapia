"""
Providing Cache Classes to cache data.
"""
import asyncio
from threading import RLock
from typing import Callable, Coroutine, Dict, Any
 
class SimpleInMemoryCache:
    """
    A thread-safe in-memory cache using the Double-Checked Locking pattern.
    """
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._lock = RLock()
 
    def get(self, key: str) -> Any | None:
        """Get an item from the cache."""
        return self._cache.get(key)
 
    def set(self, key: str, value: Any):
        """Set an item in the cache."""
        # Dictionary assignment is atomic in Python, but locks are needed
        # for consistency in more complex patterns.
        with self._lock:
            self._cache[key] = value
 
    def get_or_set_with_lock(self, key: str, value_factory: Callable[[], Any]):
        """
        Get an item from the cache. If not found, call `value_factory` to create,
        store in cache, and return. Operation is protected by a lock.
 
        Args:
            key (str): Cache key.
            value_factory (callable): A function (or lambda) with no arguments
                                      that will be called to create the value if cache miss occurs.
        """
        # Double-Checked Locking Pattern
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value
         
        with self._lock:
            # Check again inside the lock
            cached_value = self.get(key)
            if cached_value is not None:
                return cached_value
             
            # If still not found, create new value
            new_value = value_factory()
            self.set(key, new_value)
            return new_value
 
class SingletonInMemoryCache:
    _instance = None
    _lock = RLock()
 
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SingletonInMemoryCache, cls).__new__(cls)
                    # --- INITIALIZE INSTANCE ATTRIBUTES HERE ---
                    cls._instance._cache = {}
                    cls._instance._cache_lock = RLock() # A separate lock for cache access
        return cls._instance
 
    def get_or_set(self, cache_key: str, loader_func: Callable[[], Any]):
        # Quick check
        if cache_key in self._cache:
            return self._cache[cache_key]
 
        # Use instance lock
        with self._cache_lock:
            # Double-check
            if cache_key in self._cache:
                return self._cache[cache_key]
             
            new_data = loader_func()
            self._cache[cache_key] = new_data
            return new_data
         
    def clean_cache(self, cache_key: str|None = None):
        with self._cache_lock:
            if cache_key:
                if cache_key in self._cache:
                    del self._cache[cache_key]
            else:
                self._cache.clear()
         
class AsyncInMemoryCache:
    """
    An in-memory cache safe for asyncio environments.
    """
    def __init__(self):
        self._cache: dict[str, Any] = {}
        self._lock = asyncio.Lock() # <-- USING ASYNCIO.LOCK
 
    def get(self, key: str) -> Any | None:
        return self._cache.get(key)
 
    # set doesn't need to be async since dict assignment is fast
    def set(self, key: str, value: Any):
        self._cache[key] = value
 
    # This is the main method and must be async
    async def get_or_set_with_lock(self, key: str, value_factory: Callable[[], Coroutine]):
        """
        Get an item from the cache. If not found, call `value_factory` (an async function)
        to create, store in cache, and return.
        """
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value
         
        # Use asyncio lock
        async with self._lock:
            # Double-check
            cached_value = self.get(key)
            if cached_value is not None:
                return cached_value
             
            # Call async factory function
            new_value = await value_factory()
            self.set(key, new_value)
            return new_value