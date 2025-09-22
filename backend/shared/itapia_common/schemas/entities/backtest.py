from typing import Literal

# Status for backtest generation process
BACKTEST_GENERATION_STATUS = Literal["IDLE", "RUNNING", "COMPLETED", "FAILED"]

# Status for backtest context
BACKTEST_CONTEXT_STATUS = Literal[
    "IDLE", "READY_SERVE", "READY_LOAD", "PREPARING", "FAILED"
]
