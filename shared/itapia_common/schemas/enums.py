from enum import Enum

class SemanticType(str, Enum):
    """
    Định nghĩa các kiểu ngữ nghĩa cho các giá trị trong cây quy tắc.
    Điều này là trái tim của Strongly Typed Genetic Programming (STGP).
    """
    # Kiểu dữ liệu cơ bản
    NUMERICAL = 'NUMERICAL'      # Một con số bất kỳ
    BOOLEAN = 'BOOLEAN'        # Tín hiệu Đúng/Sai (1.0 / 0.0)
    
    # Kiểu ngữ nghĩa tài chính
    PRICE = 'PRICE'              # Giá trị liên quan đến giá (ví dụ: close, open)
    PERCENTAGE = 'PERCENTAGE'         # Một giá trị phần trăm (ví dụ: thay đổi giá, mức lợi nhuận)
    FINANCIAL_RATIO = 'FINANCIAL_RATIO'    # Một tỷ lệ tài chính (ví dụ: P/E)
    
    # Kiểu chỉ báo kỹ thuật
    MOMENTUM = 'MOMENTUM'           # Chỉ báo động lượng (RSI, Stochastic)
    TREND = 'TREND'              # Chỉ báo xu hướng (MACD, ADX)
    VOLATILITY = 'VOLATILITY'         # Chỉ báo biến động (ATR, Bollinger Bands)
    VOLUME = 'VOLUME'             # Chỉ báo khối lượng (OBV)
    
    # Kiểu phân tích khác
    SENTIMENT = 'SENTIMENT'         # Điểm số cảm tính
    FORECAST_PROB = 'FORECAST_PROB'      # Xác suất dự báo
    
    # Kiểu ngữ nghĩa quyết định
    DECISION_SIGNAL = 'DECISION_SIGNAL'
    RISK_LEVEL = 'RISK_LEVEL'
    OPPORTUNITY_RATING = 'OPPORTUNITY_RATING'
    
    # Kiểu đặc biệt
    ANY = 'ANY'                # Có thể là bất kỳ kiểu nào (dùng cho các toán tử linh hoạt)
    
class NodeType(str, Enum):
    CONSTANT = 'constant'
    VARIABLE = 'variable'
    OPERATOR = 'operator'
    
    ANY = 'any'