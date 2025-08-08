
class NotFoundVarPathError(Exception):
    def __init__(self, path: str):
        super().__init__()
        self.msg = f'Not found path to get var value: {path}'
        
