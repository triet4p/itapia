from datetime import datetime, timezone

class FetchException(Exception):
    def __init__(self, msg: str):
        super().__init__()
        self.msg = msg
    
DEFAULT_START_DATE = datetime(2018, 1, 1, tzinfo=timezone.utc)