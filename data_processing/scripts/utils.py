from datetime import datetime, timezone

class FetchException(Exception):
    def __init__(self, msg: str):
        super().__init__()
        self.msg = msg
    
DEFAULT_RETURN_DATE = datetime(2017, 12, 31, tzinfo=timezone.utc)

# Tiếng Anh (cho thị trường Mỹ)
UNIVERSAL_KEYWORDS_EN = [
    # Vĩ mô & Chính sách
    "US economy forecast",
    "Federal Reserve policy",
    "US inflation report CPI",
    "Non-farm payrolls",
    "US GDP growth",
    
    # Thị trường chung
    "S&P 500 outlook",
    "NASDAQ composite trends",
    "stock market sentiment",
    
    # Hàng hóa & Năng lượng
    "oil price forecast WTI crude",
    "OPEC decisions",
    
    # Ngành Công nghệ
    "semiconductor industry news",
    "artificial intelligence stocks",
    "cloud computing sector",
    
    # Ngành Tài chính
    "US banking sector health",
    
    # Ngành Chăm sóc sức khỏe
    "pharmaceutical industry FDA",
]

# Tiếng Việt (cho thị trường Việt Nam)
UNIVERSAL_KEYWORDS_VI = [
    # Vĩ mô & Chính sách
    "kinh tế vĩ mô Việt Nam",
    "lãi suất ngân hàng nhà nước",
    "lạm phát Việt Nam CPI",
    "tăng trưởng GDP Việt Nam",
    "chính sách tiền tệ",
    
    # Thị trường chung
    "nhận định thị trường chứng khoán VN-Index",
    "khối ngoại bán ròng",
    
    # Ngành Bất động sản
    "thị trường bất động sản",
    
    # Ngành Ngân hàng
    "cổ phiếu ngân hàng",
    
    # Ngành Thép
    "giá thép xây dựng HRC",
]