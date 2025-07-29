from enum import Enum, auto

class SemanticType(Enum):
    """
    Định nghĩa các kiểu ngữ nghĩa cho các giá trị trong cây quy tắc.
    Điều này là trái tim của Strongly Typed Genetic Programming (STGP).
    """
    # Kiểu dữ liệu cơ bản
    NUMERICAL = auto()      # Một con số bất kỳ
    BOOLEAN = auto()        # Tín hiệu Đúng/Sai (1.0 / 0.0)
    
    # Kiểu ngữ nghĩa tài chính
    PRICE = auto()              # Giá trị liên quan đến giá (ví dụ: close, open)
    PERCENTAGE = auto()         # Một giá trị phần trăm (ví dụ: thay đổi giá, mức lợi nhuận)
    FINANCIAL_RATIO = auto()    # Một tỷ lệ tài chính (ví dụ: P/E)
    
    # Kiểu chỉ báo kỹ thuật
    MOMENTUM = auto()           # Chỉ báo động lượng (RSI, Stochastic)
    TREND = auto()              # Chỉ báo xu hướng (MACD, ADX)
    VOLATILITY = auto()         # Chỉ báo biến động (ATR, Bollinger Bands)
    VOLUME = auto()             # Chỉ báo khối lượng (OBV)
    
    # Kiểu phân tích khác
    SENTIMENT = auto()          # Điểm số cảm tính
    FORECAST_PROB = auto()      # Xác suất dự báo
    
    # Kiểu đặc biệt
    ANY = auto()                # Có thể là bất kỳ kiểu nào (dùng cho các toán tử linh hoạt)