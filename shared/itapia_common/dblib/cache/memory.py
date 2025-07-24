import asyncio
from threading import RLock
from typing import Callable, Coroutine, Dict, Any

class SimpleInMemoryCache:
    """
    Một lớp cache in-memory an toàn luồng (thread-safe) sử dụng
    pattern Double-Checked Locking.
    """
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._lock = RLock()

    def get(self, key: str) -> Any | None:
        """Lấy một item từ cache."""
        return self._cache.get(key)

    def set(self, key: str, value: Any):
        """Đặt một item vào cache."""
        # Phép gán dictionary là atomic trong Python, nhưng lock vẫn cần thiết
        # trong các pattern phức tạp hơn. Ở đây ta dùng để nhất quán.
        with self._lock:
            self._cache[key] = value

    def get_or_set_with_lock(self, key: str, value_factory):
        """
        Lấy item từ cache. Nếu không có, gọi `value_factory` để tạo mới,
        lưu vào cache và trả về. Thao tác được bảo vệ bởi Lock.

        Args:
            key (str): Khóa cache.
            value_factory (callable): Một hàm (hoặc lambda) không có tham số,
                                      sẽ được gọi để tạo giá trị nếu cache miss.
        """
        # Double-Checked Locking Pattern
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value
        
        with self._lock:
            # Kiểm tra lại một lần nữa bên trong lock
            cached_value = self.get(key)
            if cached_value is not None:
                return cached_value
            
            # Nếu vẫn không có, tạo giá trị mới
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
                    # --- KHỞI TẠO CÁC THUỘC TÍNH INSTANCE Ở ĐÂY ---
                    cls._instance._cache = {}
                    cls._instance._cache_lock = RLock() # Một lock riêng cho việc truy cập cache
        return cls._instance

    def get_or_set(self, cache_key: str, loader_func: Callable[[], Any]):
        # Kiểm tra nhanh
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Sử dụng lock của instance
        with self._cache_lock:
            # Double-check
            if cache_key in self._cache:
                return self._cache[cache_key]
            
            new_data = loader_func()
            self._cache[cache_key] = new_data
            return new_data
        
    def clean_cache(self, cache_key: str|None = None):
        if cache_key is not None:
            self._cache[cache_key].clear()
            return
        self._cache.clear()
        
class AsyncInMemoryCache:
    """
    Một lớp cache in-memory an toàn cho môi trường asyncio.
    """
    def __init__(self):
        self._cache: dict[str, Any] = {}
        self._lock = asyncio.Lock() # <-- SỬ DỤNG ASYNCIO.LOCK

    def get(self, key: str) -> Any | None:
        return self._cache.get(key)

    # set không cần phải là async vì gán dict là nhanh
    def set(self, key: str, value: Any):
        self._cache[key] = value

    # Đây là phương thức chính và phải là async
    async def get_or_set_with_lock(self, key: str, value_factory: Callable[[], Coroutine]):
        """
        Lấy item từ cache. Nếu không có, gọi `value_factory` (một hàm async)
        để tạo mới, lưu vào cache và trả về.
        """
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value
        
        # Sử dụng lock của asyncio
        async with self._lock:
            # Double-check
            cached_value = self.get(key)
            if cached_value is not None:
                return cached_value
            
            # Gọi hàm factory bất đồng bộ
            new_value = await value_factory()
            self.set(key, new_value)
            return new_value