from datetime import datetime
from typing import NamedTuple, Literal

# THAY ĐỔI: Thêm 'SHORT' vào các loại giao dịch được hỗ trợ.
TRADE_ACTION_TYPE = Literal['LONG', 'SHORT']

# Định nghĩa các lý do thoát lệnh một cách tường minh.
EXIT_REASON_TYPE = Literal[
    'TAKE_PROFIT',   # Chạm mức chốt lời
    'STOP_LOSS',     # Chạm mức cắt lỗ
    'TIME_STOP',     # Hết thời gian nắm giữ tối đa
    'REVERSE_SIGNAL' # Có một tín hiệu ngược chiều (ví dụ: đang LONG thì có tín hiệu SELL)
]

class Trade(NamedTuple):
    """
    Một cấu trúc dữ liệu bất biến (immutable) để lưu trữ thông tin của
    một giao dịch ĐÃ HOÀN THÀNH.
    
    Hỗ trợ cả giao dịch Mua (LONG) và Bán khống (SHORT).
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
        """
        Tính toán và trả về phần trăm lợi nhuận/thua lỗ của giao dịch.
        - Giao dịch LONG có lời khi exit_price > entry_price.
        - Giao dịch SHORT có lời khi exit_price < entry_price.
        """
        if self.entry_price == 0:
            return 0.0
        
        # Logic cho giao dịch Mua (LONG)
        if self.action_type == 'LONG':
            return (self.exit_price - self.entry_price) / self.entry_price
            
        # THÊM MỚI: Logic cho giao dịch Bán khống (SHORT)
        elif self.action_type == 'SHORT':
            return (self.entry_price - self.exit_price) / self.entry_price
            
        else:
            # Sẽ không bao giờ xảy ra nếu dùng type hinting đúng
            return 0.0

    @property
    def duration_days(self) -> int:
        """
        Tính toán và trả về số ngày nắm giữ giao dịch.
        """
        return (self.exit_date - self.entry_date).days

    def __repr__(self) -> str:
        """
        Cung cấp một chuỗi đại diện rõ ràng khi in đối tượng Trade.
        """
        profit_str = f"{self.profit_pct:+.2%}" # Thêm dấu '+' cho các giá trị dương
        return (
            f"Trade(ticker={self.ticker}, type={self.action_type:<5}, " # Căn lề cho đẹp
            f"entry='{self.entry_date.date()} @ {self.entry_price:.2f}', "
            f"exit='{self.exit_date.date()} @ {self.exit_price:.2f}', "
            f"duration={self.duration_days}d, "
            f"profit={profit_str}, reason='{self.exit_reason}')"
        )

# =====================================================================
# VÍ DỤ CÁCH SỬ DỤNG MỚI
# =====================================================================
#
# from datetime import datetime, timezone
#
# # 1. Ví dụ về giao dịch SHORT thắng lợi (giá giảm)
# short_win_trade = Trade(
#     ticker="TSLA",
#     action_type="SHORT",
#     entry_date=datetime(2023, 2, 1, tzinfo=timezone.utc),
#     entry_price=200.00,
#     exit_date=datetime(2023, 2, 15, tzinfo=timezone.utc),
#     exit_price=180.00, # Giá giảm -> có lời
#     exit_reason="TAKE_PROFIT",
#     position_size_pct=0.5
# )
#
# print(short_win_trade)
# # Output: Trade(ticker=TSLA, type=SHORT, entry='2023-02-01 @ 200.00', exit='2023-02-15 @ 180.00', duration=14d, profit=+10.00%, reason='TAKE_PROFIT')
# print(f"Lợi nhuận: {short_win_trade.profit_pct:.2%}") # Output: Lợi nhuận: +10.00%
#
# # 2. Ví dụ về giao dịch SHORT thua lỗ (giá tăng)
# short_loss_trade = Trade(
#     ticker="TSLA",
#     action_type="SHORT",
#     entry_date=datetime(2023, 3, 1, tzinfo=timezone.utc),
#     entry_price=190.00,
#     exit_date=datetime(2023, 3, 5, tzinfo=timezone.utc),
#     exit_price=200.00, # Giá tăng -> thua lỗ
#     exit_reason="STOP_LOSS",
#     position_size_pct=0.5
# )
#
# print(short_loss_trade)
# # Output: Trade(ticker=TSLA, type=SHORT, entry='2023-03-01 @ 190.00', exit='2023-03-05 @ 200.00', duration=4d, profit=-5.26%, reason='STOP_LOSS')
# print(f"Lợi nhuận: {short_loss_trade.profit_pct:.2%}") # Output: Lợi nhuận: -5.26%
#
# =====================================================================

# Một cấu trúc dữ liệu nội bộ để lưu thông tin của một vị thế ĐANG MỞ.
# Nó khác với `Trade`, vì `Trade` là cho một giao dịch đã đóng.
class OpenPosition(NamedTuple):
    entry_date: datetime
    entry_price: float
    action_type: TRADE_ACTION_TYPE
    position_size_pct: float
    stop_loss_price: float
    take_profit_price: float
    time_stop_date: datetime