"""Backtest simulator for executing trading simulations."""

from datetime import datetime, timedelta
from typing import List, NamedTuple, Optional, Literal, Dict
import pandas as pd

from .trade import Trade, TRADE_ACTION_TYPE, EXIT_REASON_TYPE, OpenPosition
from .action import Action

from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger('Backtest Simulator')


class BacktestSimulator:
    """The "machine" that executes trading simulations.
    
    It iterates through price data day by day, manages one position at a time,
    and decides when to Buy/Sell based on input signals and exit rules.
    """
    
    def __init__(self, 
                 ticker: str,
                 ohlcv_df: pd.DataFrame, 
                 actions: Dict[datetime, Action],
                 trading_fee_pct: float = 0.001): # Trading fee 0.1% per side
        """Initialize the simulation engine.
        
        Args:
            ticker (str): Stock ticker symbol
            ohlcv_df (pd.DataFrame): DataFrame containing historical OHLCV data
            actions (Dict[datetime, Action]): Dictionary containing `Action` objects with datetime index
            trading_fee_pct (float, optional): Trading fee for each buy or sell transaction. 
                Defaults to 0.001 (0.1%).
        """
        self.ohlcv_df = ohlcv_df
        self.actions = actions
        self.trading_fee_pct = trading_fee_pct
        self.ticker = ticker
        
        # Internal state of the simulation engine
        self.current_position: Optional[OpenPosition] = None
        self.trade_log: List[Trade] = []

    def run(self) -> List[Trade]:
        """Run the entire simulation process from start to finish.
        
        Returns:
            List[Trade]: A log containing all executed trades
        """
        logger.debug(f"Running simulation on {len(self.ohlcv_df)} historical data points...")

        for date, row in self.ohlcv_df.iterrows():
            # Variable to check if an action was taken today
            action_taken_today = False

            # STEP 1: PRIORITIZE MANAGING OPEN POSITION
            if self.current_position:
                action_signal_for_exit = self.actions.get(date.to_pydatetime())
                self._check_and_close_position(date, row, action_signal_for_exit)
                # If position was closed, update flag
                if self.current_position is None:
                    action_taken_today = True

            # STEP 2: CONSIDER NEW SIGNAL IF NO ACTION HAS BEEN TAKEN
            if not action_taken_today:
                action_signal_for_entry = self.actions.get(date.to_pydatetime())
                if action_signal_for_entry:
                    self._process_new_signal(date, row, action_signal_for_entry)
        
        # STEP 3: CLOSE FINAL POSITION (IF ANY)
        # If after exhausting data there's still a position, close it at the last day's closing price
        if self.current_position:
            last_date = self.ohlcv_df.index[-1]
            last_close_price = self.ohlcv_df.iloc[-1]['close']
            logger.debug(f"Position still open at the end of simulation. Closing at last price {last_close_price:.2f}")
            self._close_position(last_date, last_close_price, 'TIME_STOP')

        logger.debug(f"Simulation finished. Total trades executed: {len(self.trade_log)}")
        return self.trade_log

    def _check_and_close_position(self, current_date: datetime, daily_row: pd.Series, action_signal: Optional[Action]):
        """Check all exit conditions for the open position.
        
        Args:
            current_date (datetime): Current date in simulation
            daily_row (pd.Series): Daily price data row
            action_signal (Optional[Action]): Action signal for current date
        """
        pos = self.current_position

        # Check for LONG position
        if pos.action_type == 'LONG':
            if daily_row['high'] >= pos.take_profit_price:
                self._close_position(current_date, pos.take_profit_price, 'TAKE_PROFIT')
            elif daily_row['low'] <= pos.stop_loss_price:
                self._close_position(current_date, pos.stop_loss_price, 'STOP_LOSS')
            elif action_signal and action_signal.action_type == 'SELL':
                self._close_position(current_date, daily_row['close'], 'REVERSE_SIGNAL')
            elif current_date >= pos.time_stop_date:
                self._close_position(current_date, daily_row['close'], 'TIME_STOP')
        
        # Check for SHORT position
        elif pos.action_type == 'SHORT':
            if daily_row['low'] <= pos.take_profit_price:
                self._close_position(current_date, pos.take_profit_price, 'TAKE_PROFIT')
            elif daily_row['high'] >= pos.stop_loss_price:
                self._close_position(current_date, pos.stop_loss_price, 'STOP_LOSS')
            elif action_signal and action_signal.action_type == 'BUY':
                self._close_position(current_date, daily_row['close'], 'REVERSE_SIGNAL')
            elif current_date >= pos.time_stop_date:
                self._close_position(current_date, daily_row['close'], 'TIME_STOP')

    def _process_new_signal(self, current_date: datetime, daily_row: pd.Series, action: Action):
        """Process a new signal from ActionMapper.
        
        Args:
            current_date (datetime): Current date in simulation
            daily_row (pd.Series): Daily price data row
            action (Action): Action signal to process
        """
        entry_price = daily_row['close'] * (1 + self.trading_fee_pct) # Entry price including fees/slippage

        # Open LONG position if no position exists
        if action.action_type == 'BUY' and self.current_position is None:
            self.current_position = OpenPosition(
                entry_date=current_date,
                entry_price=entry_price,
                action_type='LONG',
                position_size_pct=action.position_size_pct,
                stop_loss_price=entry_price * (1 - action.sl_pct),
                take_profit_price=entry_price * (1 + action.tp_pct),
                time_stop_date=current_date + timedelta(days=action.duration_days)
            )
            logger.debug(f"Opened LONG position on {current_date.date()} at {entry_price:.2f}")

        # Open SHORT position if no position exists
        elif action.action_type == 'SELL' and self.current_position is None:
            self.current_position = OpenPosition(
                entry_date=current_date,
                entry_price=entry_price,
                action_type='SHORT',
                position_size_pct=action.position_size_pct,
                stop_loss_price=entry_price * (1 + action.sl_pct),
                take_profit_price=entry_price * (1 - action.tp_pct),
                time_stop_date=current_date + timedelta(days=action.duration_days)
            )
            logger.debug(f"Opened SHORT position on {current_date.date()} at {entry_price:.2f}")

    def _close_position(self, exit_date: datetime, exit_price: float, reason: EXIT_REASON_TYPE):
        """Package information and record a completed trade.
        
        Args:
            exit_date (datetime): Exit date for the position
            exit_price (float): Exit price for the position
            reason (EXIT_REASON_TYPE): Reason for closing the position
        """
        pos = self.current_position
        
        # Actual exit price after deducting fees/slippage
        actual_exit_price = exit_price * (1 - self.trading_fee_pct)
        
        ticker = self.ticker
        
        completed_trade = Trade(
            ticker=ticker, # Get ticker from df if available
            action_type=pos.action_type,
            entry_date=pos.entry_date,
            entry_price=pos.entry_price,
            exit_date=exit_date,
            exit_price=actual_exit_price,
            exit_reason=reason,
            position_size_pct=pos.position_size_pct
        )
        
        self.trade_log.append(completed_trade)
        logger.debug(f"Closed {pos.action_type} position: {completed_trade}")
        
        # Reset current position
        self.current_position = None