# itapia_common/contracts/schemas/entities/advisor.py

from pydantic import BaseModel, Field
from typing import List, Dict, Any

class TriggeredRuleInfo(BaseModel):
    """
    Thông tin tóm tắt về một quy tắc (Rule) đã được kích hoạt.
    'Kích hoạt' có nghĩa là quy tắc đó đã trả về một điểm số khác 0.
    """
    rule_id: str = Field(..., description="ID của quy tắc.")
    name: str = Field(..., description="Tên của quy tắc để con người đọc.")
    score: float = Field(..., description="Điểm số mà quy tắc trả về (đã chuẩn hóa).")
    purpose: str = Field(..., description="Mục đích của quy tắc, ví dụ: 'DECISION_SIGNAL'.")
    
    class Config:
        from_attributes = True

class AggregatedScoreInfo(BaseModel):
    """
    Thông tin về các điểm số đã được tổng hợp từ các bộ quy tắc.
    """
    raw_decision_score: float = Field(..., description="Điểm số quyết định thô (trước khi có MetaRule).")
    raw_risk_score: float = Field(..., description="Điểm số rủi ro thô (trước khi có MetaRule).")
    raw_opportunity_score: float = Field(..., description="Điểm số cơ hội thô (trước khi có MetaRule).")
    
    class Config:
        from_attributes = True

class FinalRecommendation(BaseModel):
    """
    Thông tin về khuyến nghị cuối cùng sau khi đã qua tất cả các tầng.
    """
    # Điểm số cuối cùng sau khi đã qua MetaRule
    final_score: float = Field(..., description="Điểm số cuối cùng sau khi đã tổng hợp và cá nhân hóa.")
    purpose: str
    label: str
    # Nhãn diễn giải từ điểm số
    final_recommend: str = Field(..., description='Final recommend')
    
    triggered_rules: List[TriggeredRuleInfo] = Field(..., description="Danh sách các quy tắc đã được kích hoạt và đóng góp vào kết quả.")

    class Config:
        from_attributes = True


class AdvisorReportSchema(BaseModel):
    """
    Schema cho báo cáo tổng hợp cuối cùng từ Advisor Module.
    Đây là "hợp đồng" dữ liệu chính, được sử dụng cả trong nội bộ
    và trả về cho API trong giai đoạn MVP.
    """
    # --- Phần Kết luận Chính (Quan trọng nhất cho người dùng) ---
    final_decision: FinalRecommendation = Field(..., description="Khuyến nghị Quyết định cuối cùng.")
    final_risk: FinalRecommendation = Field(..., description="Đánh giá Rủi ro cuối cùng.")
    final_opportunity: FinalRecommendation = Field(..., description="Đánh giá Cơ hội cuối cùng.")
    
    # --- Phần Bằng chứng và Diễn giải (Cho việc debug và XAI) ---
    aggregated_scores: AggregatedScoreInfo = Field(..., description="Các điểm số tổng hợp trước khi qua MetaRule.")
    # --- Metadata của Báo cáo ---
    ticker: str = Field(..., description="Mã cổ phiếu được phân tích.")
    generated_at_utc: str = Field(..., description="Thời gian tạo báo cáo (ISO format).")
    generated_timestamp: int = Field(..., description='Generate with timestamp')

    class Config:
        from_attributes = True