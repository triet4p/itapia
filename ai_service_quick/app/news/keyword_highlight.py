from typing import List, Union, Set

# Import các schema Pydantic đã định nghĩa
from itapia_common.dblib.schemas.reports.news import (
    KeywordHighlightingReport
)

class WordBasedKeywordHighlightingModel:
    """
    Trích xuất các từ khóa tình cảm (bằng chứng) từ văn bản
    dựa trên các bộ từ điển được cung cấp.
    """
    def __init__(self, positive_dictionary: Set[str], negative_dictionary: Set[str]):
        """
        Khởi tạo model với các bộ từ điển đã được tải.

        Args:
            positive_dictionary (Set[str]): Một set chứa các từ tích cực.
            negative_dictionary (Set[str]): Một set chứa các từ tiêu cực.
        """
        self.positive_words = positive_dictionary
        self.negative_words = negative_dictionary

    def extract(self, texts: List[str]) -> List[KeywordHighlightingReport]:
        """
        Trích xuất bằng chứng tình cảm cho một hoặc nhiều văn bản (đã được tiền xử lý).

        Args:
            texts (Union[str, List[str]]): Một chuỗi hoặc một danh sách các chuỗi đã được chuẩn hóa.

        Returns:
            Union[KeywordHighlightingEvidence, List[KeywordHighlightingEvidence]]: Bằng chứng trích xuất được.
        """

        reports = []
        for text in texts:
            # Bẻ văn bản thành các từ duy nhất để chỉ highlight mỗi từ một lần
            words_in_text = set(text.split())
            
            # Tìm các từ trùng với từ điển
            found_positive = [
                word
                for word in words_in_text if word in self.positive_words
            ]
            found_negative = [
                word 
                for word in words_in_text if word in self.negative_words
            ]
            
            reports.append(KeywordHighlightingReport(
                positive_keywords=found_positive,
                negative_keywords=found_negative
            ))

        return reports