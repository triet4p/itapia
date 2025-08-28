from datetime import datetime, timedelta
from typing import List, NamedTuple, Optional, Literal, Dict
import pandas as pd

from .trade import Trade, TRADE_ACTION_TYPE, EXIT_REASON_TYPE, OpenPosition
from .action import Action

from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger('Backtest Simulator')

class BacktestSimulator:
    """
    "Cỗ máy" thực thi mô phỏng giao dịch.
    
    Nó lặp qua dữ liệu giá ngày qua ngày, quản lý một vị thế tại một thời điểm,
    và quyết định khi nào Mua/Bán dựa trên các tín hiệu đầu vào và quy tắc thoát lệnh.
    """
    def __init__(self, 
                 ticker: str,
                 ohlcv_df: pd.DataFrame, 
                 actions: Dict[datetime, Action],
                 trading_fee_pct: float = 0.001): # Phí giao dịch 0.1% mỗi chiều
        """
        Khởi tạo bộ mô phỏng.
        
        Args:
            ohlcv_df (pd.DataFrame): DataFrame chứa dữ liệu OHLCV lịch sử.
            actions_series (pd.Series): Series chứa các đối tượng `Action` với index là datetime.
            trading_fee_pct (float): Phí giao dịch cho mỗi lần mua hoặc bán.
        """
        self.ohlcv_df = ohlcv_df
        self.actions = actions
        self.trading_fee_pct = trading_fee_pct
        self.ticker = ticker
        
        # Trạng thái nội bộ của bộ mô phỏng
        self.current_position: Optional[OpenPosition] = None
        self.trade_log: List[Trade] = []

    def run(self) -> List[Trade]:
        """
        Chạy toàn bộ quá trình mô phỏng từ đầu đến cuối.
        
        Returns:
            List[Trade]: Một nhật ký chứa tất cả các giao dịch đã được thực hiện.
        """
        logger.debug(f"Running simulation on {len(self.ohlcv_df)} historical data points...")

        for date, row in self.ohlcv_df.iterrows():
            # Biến để kiểm tra xem một hành động đã được thực hiện trong ngày chưa
            action_taken_today = False

            # BƯỚC 1: ƯU TIÊN QUẢN LÝ VỊ THẾ ĐANG MỞ
            if self.current_position:
                action_signal_for_exit = self.actions.get(date.to_pydatetime())
                self._check_and_close_position(date, row, action_signal_for_exit)
                # Nếu vị thế đã được đóng, cập nhật cờ
                if self.current_position is None:
                    action_taken_today = True

            # BƯỚC 2: XEM XÉT TÍN HIỆU MỚI NẾU CHƯA CÓ HÀNH ĐỘNG NÀO
            if not action_taken_today:
                action_signal_for_entry = self.actions.get(date.to_pydatetime())
                if action_signal_for_entry:
                    self._process_new_signal(date, row, action_signal_for_entry)
        
        # BƯỚC 3: ĐÓNG VỊ THẾ CUỐI CÙNG (NẾU CÓ)
        # Nếu sau khi hết dữ liệu mà vẫn còn vị thế, đóng nó ở giá đóng cửa ngày cuối cùng.
        if self.current_position:
            last_date = self.ohlcv_df.index[-1]
            last_close_price = self.ohlcv_df.iloc[-1]['close']
            logger.debug(f"Position still open at the end of simulation. Closing at last price {last_close_price:.2f}")
            self._close_position(last_date, last_close_price, 'TIME_STOP')

        logger.debug(f"Simulation finished. Total trades executed: {len(self.trade_log)}")
        return self.trade_log

    def _check_and_close_position(self, current_date: datetime, daily_row: pd.Series, action_signal: Optional[Action]):
        """Kiểm tra tất cả các điều kiện thoát lệnh cho vị thế đang mở."""
        pos = self.current_position

        # Kiểm tra cho vị thế MUA (LONG)
        if pos.action_type == 'LONG':
            if daily_row['high'] >= pos.take_profit_price:
                self._close_position(current_date, pos.take_profit_price, 'TAKE_PROFIT')
            elif daily_row['low'] <= pos.stop_loss_price:
                self._close_position(current_date, pos.stop_loss_price, 'STOP_LOSS')
            elif action_signal and action_signal.action_type == 'SELL':
                self._close_position(current_date, daily_row['close'], 'REVERSE_SIGNAL')
            elif current_date >= pos.time_stop_date:
                self._close_position(current_date, daily_row['close'], 'TIME_STOP')
        
        # Kiểm tra cho vị thế BÁN KHỐNG (SHORT)
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
        """Xử lý một tín hiệu mới từ ActionMapper."""
        entry_price = daily_row['close'] * (1 + self.trading_fee_pct) # Giá vào lệnh đã tính phí/trượt giá

        # Mở vị thế MUA (LONG) nếu chưa có vị thế nào
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

        # Mở vị thế BÁN KHỐNG (SHORT) nếu chưa có vị thế nào
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
        """Đóng gói thông tin và ghi nhận một giao dịch đã hoàn thành."""
        pos = self.current_position
        
        # Giá thoát lệnh thực tế sau khi trừ phí/trượt giá
        actual_exit_price = exit_price * (1 - self.trading_fee_pct)
        
        ticker = self.ticker
        
        completed_trade = Trade(
            ticker=ticker, # Lấy ticker từ df nếu có
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
        
        # Reset vị thế hiện tại
        self.current_position = None