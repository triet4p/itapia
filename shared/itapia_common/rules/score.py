# itapia_common/rules/score.py

"""
Module này chứa các lớp chịu trách nhiệm tổng hợp và diễn giải
các điểm số thô (raw scores) từ các bộ quy tắc.
"""

from typing import List, Dict, Tuple

# Import các định nghĩa ngưỡng từ file chúng ta vừa tạo
from .final_thresholds import (
    FinalThreshold,
    DECISION_THRESHOLDS,
    RISK_THRESHOLDS,
    OPPORTUNITY_THRESHOLDS
)
from itapia_common.schemas.enums import SemanticType

# ===================================================================
# == LỚP 3/10: SCORE AGGREGATOR
# ===================================================================

class ScoreAggregator:
    """
    Thực hiện logic tổng hợp một danh sách các điểm số thô thành một điểm số duy nhất.
    Lớp này không biết về mục đích (purpose), nó chỉ thực hiện các phép toán.
    """

    def average(self, scores: List[float]) -> float:
        """Tính trung bình cộng của các điểm số."""
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def weighted_average(self, scores: List[float], weights: List[float]) -> float:
        """Tính trung bình có trọng số."""
        if not scores:
            return 0.0
        if len(scores) != len(weights):
            raise ValueError("Số lượng điểm số và trọng số phải bằng nhau.")
        
        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        total_weight = sum(weights)
        
        if total_weight == 0:
            return 0.0
        return weighted_sum / total_weight

    def get_max_score(self, scores: List[float]) -> float:
        """Lấy điểm số có giá trị tuyệt đối lớn nhất, giữ nguyên dấu."""
        if not scores:
            return 0.0
        return max(scores, key=abs)

    def get_highest_score(self, scores: List[float]) -> float:
        """Lấy điểm số cao nhất (hữu ích cho Rủi ro và Cơ hội)."""
        if not scores:
            return 0.0
        return max(scores)

# ===================================================================
# == LỚP 4/10: SCORE FINAL MAPPER
# ===================================================================

class ScoreFinalMapper:
    """
    ánh xạ một điểm số cuối cùng (đã được tổng hợp) sang một nhãn kết luận
    có ý nghĩa cho con người, dựa trên các ngưỡng đã được định nghĩa trước.
    """
    
    FINAL_MAPPER_TEMPLATE = "Threshold match is {name}, which mean {description}."
    
    def __init__(self):
        # Tạo một map từ purpose sang bộ ngưỡng tương ứng để dễ tra cứu
        self._threshold_map: Dict[SemanticType, List[FinalThreshold]] = {
            SemanticType.DECISION_SIGNAL: DECISION_THRESHOLDS,
            SemanticType.RISK_LEVEL: RISK_THRESHOLDS,
            SemanticType.OPPORTUNITY_RATING: OPPORTUNITY_THRESHOLDS,
        }

    def map(self, score: float, purpose: SemanticType) -> str:
        """
        Thực hiện logic mapping chính.

        Args:
            score (float): Điểm số cuối cùng cần được diễn giải.
            purpose (SemanticType): Mục đích của điểm số, để chọn đúng bộ ngưỡng.

        Returns:
            Tuple[str, str]: Một tuple chứa (tên định danh, chuỗi mô tả đầy đủ).
                             Ví dụ: ('THRESHOLD_DECISION_BUY_STRONG', 'Strong indication to buy')
        """
        thresholds = self._threshold_map.get(purpose)
        
        if thresholds is None:
            raise ValueError(f"Không tìm thấy bộ ngưỡng nào cho mục đích: {purpose.name}")

        # Tìm ngưỡng phù hợp nhất
        # Logic: Tìm ngưỡng gần nhất mà không vượt quá điểm số đó
        best_match: FinalThreshold = thresholds[0] # Bắt đầu với giá trị thấp nhất
        
        for threshold in thresholds:
            if score >= threshold.value:
                best_match = threshold
            else:
                # Vì danh sách đã được sắp xếp, ta có thể dừng ngay khi gặp ngưỡng lớn hơn
                break

        return ScoreFinalMapper.FINAL_MAPPER_TEMPLATE.format(name=best_match.name, description=best_match.description)