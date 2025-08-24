
class NotFoundVarPathError(Exception):
    """Exception raised when a variable path cannot be found in the report."""
    
    def __init__(self, path: str):
        """Initialize the exception with a path.
        
        Args:
            path (str): The path that could not be found
        """
        super().__init__()
        self.msg = f'Not found path to get var value: {path}'
        
