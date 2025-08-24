"""Utility functions and constants for data processing scripts.

This module contains utility classes, constants, and functions used across
the data processing scripts for fetching and processing financial data.
"""

from datetime import datetime, timezone

class FetchException(Exception):
    """Custom exception for data fetching errors."""
    
    def __init__(self, msg: str):
        """Initialize the exception with a message.
        
        Args:
            msg (str): Error message.
        """
        super().__init__()
        self.msg = msg
    
DEFAULT_RETURN_DATE = datetime(2017, 12, 31, tzinfo=timezone.utc)

# English keywords (for US market)
UNIVERSAL_KEYWORDS_EN = [
    # Macro & Policy
    "US economy forecast",
    "Federal Reserve policy",
    "US inflation report CPI",
    "Non-farm payrolls",
    "US GDP growth",
    
    # General Market
    "S&P 500 outlook",
    "NASDAQ composite trends",
    "stock market sentiment",
    
    # Commodities & Energy
    "oil price forecast WTI crude",
    "OPEC decisions",
    
    # Technology Sector
    "semiconductor industry news",
    "artificial intelligence stocks",
    "cloud computing sector",
    
    # Financial Sector
    "US banking sector health",
    
    # Healthcare Sector
    "pharmaceutical industry FDA",
]

UNIVERSAL_TOPIC_EN = [
    'WORLD',
    'NATION',
    'BUSINESS',
    'TECHNOLOGY',
    'HEALTH',
    'POLITICS',
    'FINANCE',
    'ENERGY',
    'ECONOMY'
]

# Vietnamese keywords (for Vietnamese market)
UNIVERSAL_KEYWORDS_VI = [
    # Macro & Policy
    "kinh tế vĩ mô Việt Nam",
    "lãi suất ngân hàng nhà nước",
    "lạm phát Việt Nam CPI",
    "tăng trưởng GDP Việt Nam",
    "chính sách tiền tệ",
    
    # General Market
    "nhận định thị trường chứng khoán VN-Index",
    "khối ngoại bán ròng",
    
    # Real Estate Sector
    "thị trường bất động sản",
    
    # Banking Sector
    "cổ phiếu ngân hàng",
    
    # Steel Sector
    "giá thép xây dựng HRC",
]