class AuthError(Exception):
    def __init__(self, msg: str):
        super().__init__()
        self.msg = msg
        
class NoDataError(Exception):
    def __init__(self, msg: str):
        super().__init__()
        self.msg = msg
        
class DBError(Exception):
    def __init__(self, msg: str):
        super().__init__()
        self.msg = msg
    
class ServerCredError(Exception):
    def __init__(self, detail: str, header: any):
        super().__init__()
        self.detail = detail
        self.header = header