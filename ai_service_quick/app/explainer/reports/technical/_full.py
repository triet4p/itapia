from typing import List, Dict, Any

# Import schema cấp cao nhất
from itapia_common.schemas.entities.reports.technical import TechnicalReport

# Import các explainer chuyên biệt mà chúng ta đã xây dựng
from .daily import DailyAnalysisExplainer
from .intraday import IntradayAnalysisExplainer

class TechnicalAnalysisExplainer:
    """
    Tạo ra một bản tóm tắt bằng ngôn ngữ tự nhiên cho toàn bộ TechnicalReport,
    bằng cách điều phối các explainer chuyên biệt cho daily và intraday.
    """
    _TEMPLATE = """
Technical Analysis Summary:

{daily_summary}

{intraday_summary}
    """.strip() # Dùng strip() để loại bỏ khoảng trắng thừa ở đầu

    def __init__(self):
        # Khởi tạo các "chuyên gia" giải thích cấp dưới
        self.daily_explainer = DailyAnalysisExplainer()
        self.intraday_explainer = IntradayAnalysisExplainer()

    def explain(self, report: TechnicalReport) -> str:
        """
        Tạo ra một đoạn văn giải thích hoàn chỉnh dựa trên loại báo cáo được yêu cầu.

        Args:
            report (TechnicalReport): Đối tượng báo cáo Pydantic tổng hợp.

        Returns:
            str: Một chuỗi văn bản giải thích.
        """
        daily_summary = ""
        intraday_summary = ""

        # Logic để quyết định phần nào của báo cáo sẽ được giải thích,
        # dựa trên trường 'report_type'.
        
        if report.report_type in ['daily', 'all'] and report.daily_report:
            daily_summary = self.daily_explainer.explain(report.daily_report)
        
        if report.report_type in ['intraday', 'all'] and report.intraday_report:
            intraday_summary = self.intraday_explainer.explain(report.intraday_report)

        # Nếu không có báo cáo nào được tạo (ví dụ: report_type là 'daily' nhưng daily_report là None)
        if not daily_summary and not intraday_summary:
            return "No technical analysis data is available to generate an explanation."

        return self._TEMPLATE.format(
            daily_summary=daily_summary,
            intraday_summary=intraday_summary
        ).strip() # Dùng strip() một lần nữa để xóa các dòng trống nếu một trong hai summary rỗng