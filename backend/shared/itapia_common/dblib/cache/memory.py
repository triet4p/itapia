"""
Provides cache classes for caching data in memory.
"""
import asyncio
from threading import RLock
from typing import Callable, Coroutine, Dict, Any
 
class SimpleInMemoryCache:
    """A thread-safe in-memory cache using the Double-Checked Locking pattern."""
    
    def __init__(self):
        """Initialize the cache with an empty dictionary and a reentrant lock."""
        self._cache: Dict[str, Any] = {}
        self._lock = RLock()
 
    def get(self, key: str) -> Any | None:
        """Get an item from the cache.

        Args:
            key (str): The key to look up in the cache.

        Returns:
            Any | None: The cached value if found, otherwise None.
        """
        return self._cache.get(key)
 
    def set(self, key: str, value: Any):
        """Set an item in the cache.

        Args:
            key (str): The key to store the value under.
            value (Any): The value to store in the cache.
        """
        # Dictionary assignment is atomic in Python, but locks are needed
        # for consistency in more complex patterns.
        with self._lock:
            self._cache[key] = value
 
    def get_or_set_with_lock(self, key: str, value_factory: Callable[[], Any]):
        """Get an item from the cache. If not found, call `value_factory` to create,
        store in cache, and return. Operation is protected by a lock.

        This method implements the Double-Checked Locking pattern to minimize lock contention.

        Args:
            key (str): Cache key.
            value_factory (Callable[[], Any]): A function with no arguments that will be 
                                              called to create the value if cache miss occurs.

        Returns:
            Any: The cached value or the newly created value.
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
    """A thread-safe singleton in-memory cache implementation."""
    
    _instance = None
    _lock = RLock()
 
    def __new__(cls):
        """Create a new instance of the class or return the existing one (singleton pattern).

        Returns:
            SingletonInMemoryCache: The singleton instance of the cache.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SingletonInMemoryCache, cls).__new__(cls)
                    # Initialize instance attributes
                    cls._instance._cache = {}
                    cls._instance._cache_lock = RLock()  # A separate lock for cache access
        return cls._instance
 
    def get_or_set(self, cache_key: str, loader_func: Callable[[], Any]):
        """Get an item from the cache or load it using the provided function if not found.

        This method implements the Double-Checked Locking pattern to minimize lock contention.

        Args:
            cache_key (str): The key to look up in the cache.
            loader_func (Callable[[], Any]): A function that will be called to load the data
                                           if it's not found in the cache.

        Returns:
            Any: The cached or newly loaded data.
        """
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
        """Clear cached data either for a specific key or all data.

        Args:
            cache_key (str | None, optional): The key to remove from cache. 
                                            If None, clears all cache data. Defaults to None.
        """
        with self._cache_lock:
            if cache_key:
                if cache_key in self._cache:
                    del self._cache[cache_key]
            else:
                self._cache.clear()
         
class AsyncInMemoryCache:
    """An in-memory cache safe for asyncio environments."""
    
    def __init__(self):
        """Initialize the cache with an empty dictionary and an asyncio lock."""
        self._cache: dict[str, Any] = {}
        self._lock = asyncio.Lock()  # Using asyncio.Lock for async safety
 
    def get(self, key: str) -> Any | None:
        """Get an item from the cache.

        Args:
            key (str): The key to look up in the cache.

        Returns:
            Any | None: The cached value if found, otherwise None.
        """
        return self._cache.get(key)
 
    def set(self, key: str, value: Any):
        """Set an item in the cache.

        Args:
            key (str): The key to store the value under.
            value (Any): The value to store in the cache.
        """
        # set doesn't need to be async since dict assignment is fast
        self._cache[key] = value
 
    async def get_or_set_with_lock(self, key: str, value_factory: Callable[[], Coroutine]):
        """Get an item from the cache. If not found, call `value_factory` (an async function)
        to create, store in cache, and return.

        This method implements the Double-Checked Locking pattern to minimize lock contention.

        Args:
            key (str): Cache key.
            value_factory (Callable[[], Coroutine]): An async function that will be called to 
                                                   create the value if cache miss occurs.

        Returns:
            Any: The cached value or the newly created value.
        """
        # This is the main method and must be async
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