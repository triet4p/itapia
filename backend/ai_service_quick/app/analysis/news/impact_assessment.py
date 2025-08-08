from typing import List, Set, Union, Literal, Tuple
from itapia_common.schemas.entities.analysis.news import ImpactAssessmentReport
# ... (Import schema và keywords giữ nguyên) ...

ImpactLabel = Literal['low', 'moderate', 'high', 'unknown']

# app/news/impact_keywords.py

class WordBasedImpactAssessmentModel:
    def __init__(self, high_impact_dictionary: Set[str],
                 moderate_impact_dictionary: Set[str],
                 low_impact_dictionary: Set[str]):
        self.high_impact_dictionary = high_impact_dictionary
        self.moderate_impact_dictionary = moderate_impact_dictionary
        self.low_impact_dictionary = low_impact_dictionary

    def _find_matched_keywords(self, text: str) -> Tuple[ImpactLabel, List[str]]:
        """
        Một hàm helper quét văn bản và trả về cả nhãn và danh sách từ khóa khớp.
        """
        # Quét tìm các từ khóa High Impact
        high_matches = [keyword for keyword in self.high_impact_dictionary if keyword in text]
        if high_matches:
            return 'high', high_matches # Trả về ngay khi tìm thấy mức cao nhất

        # Nếu không, quét tìm các từ khóa Medium Impact
        medium_matches = [keyword for keyword in self.moderate_impact_dictionary if keyword in text]
        if medium_matches:
            return 'moderate', medium_matches

        # Nếu không có gì khớp
        low_matches = [keyword for keyword in self.low_impact_dictionary if keyword in text]
        if low_matches:
            return 'low', low_matches
        
        return 'unknown', []

    def assess(self, texts: List[str]) -> List[ImpactAssessmentReport]:
        """
        Đánh giá tác động cho một hoặc nhiều văn bản (đã được tiền xử lý/chuẩn hóa).
        """
        reports = []
        for text in texts:
            # Gọi hàm helper để lấy cả hai thông tin
            label, matched_keywords = self._find_matched_keywords(text)
            
            reports.append(ImpactAssessmentReport(
                level=label,
                words=matched_keywords
            ))

        return reports