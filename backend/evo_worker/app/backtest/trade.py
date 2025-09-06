"""Trading data structures for backtesting."""

from datetime import datetime
from typing import NamedTuple, Literal

# CHANGE: Add 'SHORT' to supported trade actions.
TRADE_ACTION_TYPE = Literal['LONG', 'SHORT']

# Define exit reasons explicitly.
EXIT_REASON_TYPE = Literal[
    'TAKE_PROFIT',   # Hit take profit level
    'STOP_LOSS',     # Hit stop loss level
    'TIME_STOP',     # Exceeded maximum holding time
    'REVERSE_SIGNAL' # Received opposite signal (e.g., LONG position receives SELL signal)
]

class Trade(NamedTuple):
    """An immutable data structure to store information about a COMPLETED trade.
    
    Supports both Buy (LONG) and Short Sell (SHORT) trades.
    """
    ticker: str
    action_type: TRADE_ACTION_TYPE
    
    entry_date: datetime
    entry_price: float
    
    exit_date: datetime
    exit_price: float
    
    exit_reason: EXIT_REASON_TYPE
    
    position_size_pct: float
    
    @property
    def profit_pct(self) -> float:
        """Calculate and return the percentage profit/loss of the trade.
        - LONG trades profit when exit_price > entry_price.
        - SHORT trades profit when exit_price < entry_price.
        
        Returns:
            float: Percentage profit/loss of the trade
        """
        if self.entry_price == 0:
            return 0.0
        
        # Logic for Buy (LONG) trades
        if self.action_type == 'LONG':
            return (self.exit_price - self.entry_price) / self.entry_price
            
        # NEW: Logic for Short Sell (SHORT) trades
        elif self.action_type == 'SHORT':
            return (self.entry_price - self.exit_price) / self.entry_price
            
        else:
            # Should never happen with proper type hinting
            return 0.0

    @property
    def duration_days(self) -> int:
        """Calculate and return the number of days the trade was held.
        
        Returns:
            int: Number of days the trade was held
        """
        return (self.exit_date - self.entry_date).days

    def __repr__(self) -> str:
        """Provide a clear string representation when printing Trade objects.
        
        Returns:
            str: String representation of the trade
        """
        profit_str = f"{self.profit_pct:+.2%}" # Add '+' sign for positive values
        return (
            f"Trade(ticker={self.ticker}, type={self.action_type:<5}, " # Left-align for better formatting
            f"entry='{self.entry_date.date()} @ {self.entry_price:.2f}', "
            f"exit='{self.exit_date.date()} @ {self.exit_price:.2f}', "
            f"duration={self.duration_days}d, "
            f"profit={profit_str}, reason='{self.exit_reason}')"
        )

# =====================================================================
# EXAMPLE USAGE
# =====================================================================
#
# from datetime import datetime, timezone
#
# # 1. Example of winning SHORT trade (price goes down)
# short_win_trade = Trade(
#     ticker="TSLA",
#     action_type="SHORT",
#     entry_date=datetime(2023, 2, 1, tzinfo=timezone.utc),
#     entry_price=200.00,
#     exit_date=datetime(2023, 2, 15, tzinfo=timezone.utc),
#     exit_price=180.00, # Price goes down -> profit
#     exit_reason="TAKE_PROFIT",
#     position_size_pct=0.5
# )
#
# print(short_win_trade)
# # Output: Trade(ticker=TSLA, type=SHORT, entry='2023-02-01 @ 200.00', exit='2023-02-15 @ 180.00', duration=14d, profit=+10.00%, reason='TAKE_PROFIT')
# print(f"Profit: {short_win_trade.profit_pct:.2%}") # Output: Profit: +10.00%
#
# # 2. Example of losing SHORT trade (price goes up)
# short_loss_trade = Trade(
#     ticker="TSLA",
#     action_type="SHORT",
#     entry_date=datetime(2023, 3, 1, tzinfo=timezone.utc),
#     entry_price=190.00,
#     exit_date=datetime(2023, 3, 5, tzinfo=timezone.utc),
#     exit_price=200.00, # Price goes up -> loss
#     exit_reason="STOP_LOSS",
#     position_size_pct=0.5
# )
#
# print(short_loss_trade)
# # Output: Trade(ticker=TSLA, type=SHORT, entry='2023-03-01 @ 190.00', exit='2023-03-05 @ 200.00', duration=4d, profit=-5.26%, reason='STOP_LOSS')
# print(f"Profit: {short_loss_trade.profit_pct:.2%}") # Output: Profit: -5.26%
#
# =====================================================================

# An internal data structure to store information about an OPEN position.
# It differs from `Trade`, because `Trade` is for a CLOSED trade.
class OpenPosition(NamedTuple):
    """Represents an open trading position.
    
    Different from `Trade`, which represents a completed trade.
    """
    entry_date: datetime
    entry_price: float
    action_type: TRADE_ACTION_TYPE
    position_size_pct: float
    stop_loss_price: float
    take_profit_price: float
    time_stop_date: datetime