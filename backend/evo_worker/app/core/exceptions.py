class BacktestError(Exception):
    def __init__(self, msg: str):
        super().__init__()
        self.msg = msg
