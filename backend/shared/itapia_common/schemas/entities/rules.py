from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Literal, Optional

from enum import Enum

class SemanticType(str, Enum):
    """
    Định nghĩa các kiểu ngữ nghĩa cho các giá trị trong cây quy tắc.
    Điều này là trái tim của Strongly Typed Genetic Programming (STGP).
    """
    # Kiểu dữ liệu cơ bản
    NUMERICAL = 'NUMERICAL'      # Một con số bất kỳ, ko có ý nghĩa
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
    ANY_NUMERIC = 'ANY_NUMERIC'        # Có thể là bất kỳ kiểu số nào (dùng cho các toán tử linh hoạt)
    
    def __init__(self, value: str):
        self.concreates: List[SemanticType] = []
        
SemanticType.ANY.concreates = [SemanticType.NUMERICAL, SemanticType.PRICE,
                               SemanticType.PERCENTAGE, SemanticType.FINANCIAL_RATIO,
                               SemanticType.MOMENTUM, SemanticType.TREND,
                               SemanticType.VOLATILITY, SemanticType.VOLUME,
                               SemanticType.SENTIMENT, SemanticType.FORECAST_PROB,
                               SemanticType.BOOLEAN]

SemanticType.ANY_NUMERIC.concreates = [SemanticType.NUMERICAL, SemanticType.PRICE,
                                       SemanticType.PERCENTAGE, SemanticType.FINANCIAL_RATIO,
                                       SemanticType.MOMENTUM, SemanticType.TREND,
                                       SemanticType.VOLATILITY, SemanticType.VOLUME,
                                       SemanticType.SENTIMENT, SemanticType.FORECAST_PROB]
        
    
class NodeType(str, Enum):
    CONSTANT = 'constant'
    VARIABLE = 'variable'
    OPERATOR = 'operator'
    
    ANY = 'any'

class NodeEntity(BaseModel):
    node_name: str
    children: Optional[List['NodeEntity']] = Field(default=None)
     
    class Config:
        from_attributes = True

class NodeSpecEntity(BaseModel):
    node_name: str
    description: str
    node_type: NodeType
    return_type: SemanticType = Field(..., description='return type of a nodes')
    args_type: Optional[List[SemanticType]] = Field(default=None, description='Argument type, only need for operator node')
    
    class Config:
        from_attributes = True
        
class RuleEntity(BaseModel):
    rule_id: str
    name: str
    description: str
    purpose: SemanticType
    version: float
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Định nghĩa quy tắc được giữ dưới dạng dictionary
    root: NodeEntity
    
    class Config:
        from_attributes = True
        
class ExplainationRuleEntity(RuleEntity):
    explain: str
    