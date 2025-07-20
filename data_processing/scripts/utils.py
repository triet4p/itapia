from datetime import datetime, timezone

class FetchException(Exception):
    def __init__(self, msg: str):
        super().__init__()
        self.msg = msg
    
DEFAULT_RETURN_DATE = datetime(2017, 12, 31, tzinfo=timezone.utc)