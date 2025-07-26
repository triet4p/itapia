class PreloadCacheError(Exception):
    """Ngoại lệ tùy chỉnh cho các lỗi xảy ra trong quá trình preload cache."""
    def __init__(self, module_name: str, failed_elements: list):
        self.module_name = module_name
        self.failed_elements = failed_elements
        message = (
            f"Failed to preload caches for module '{module_name}'. "
            f"Failed elements: {', '.join(failed_elements)}"
        )
        super().__init__(message)