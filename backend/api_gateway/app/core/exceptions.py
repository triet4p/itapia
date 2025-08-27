class AuthError(Exception):
    """Exception raised for authentication errors."""
    def __init__(self, msg: str):
        super().__init__()
        self.msg = msg
        
class NoDataError(Exception):
    """Exception raised when no data is found."""
    def __init__(self, msg: str):
        super().__init__()
        self.msg = msg
        
class DBError(Exception):
    """Exception raised for database errors."""
    def __init__(self, msg: str):
        super().__init__()
        self.msg = msg
    
class ServerCredError(Exception):
    """Exception raised for server credential errors."""
    def __init__(self, detail: str, header: any):
        super().__init__()
        self.detail = detail
        self.header = header