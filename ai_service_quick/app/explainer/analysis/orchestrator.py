from typing import Literal, Union

# Import schema báo cáo cấp cao nhất và các explainer của từng module
from itapia_common.schemas.entities.analysis import QuickCheckAnalysisReport

from .technical import TechnicalAnalysisExplainer
from .news import NewsAnalysisExplainer
from .forecasting import ForecastingExplainer

# Định nghĩa kiểu cho các loại báo cáo có thể yêu cầu
ExplainReportType = Literal['technical', 'news', 'forecasting', 'all']

class AnalysisExplainerOrchestrator:
    """
    Điều phối việc tạo ra các bản tóm tắt bằng ngôn ngữ tự nhiên
    cho các phần khác nhau của QuickCheckReport.
    """
    def __init__(self):
        # Khởi tạo tất cả các "trưởng phòng" explainer
        self.tech_explainer = TechnicalAnalysisExplainer()
        self.news_explainer = NewsAnalysisExplainer()
        self.forecasting_explainer = ForecastingExplainer()

    def explain(self, 
                report: QuickCheckAnalysisReport, 
                report_type: ExplainReportType = 'all'
               ) -> str:
        """
        Tạo ra một chuỗi văn bản giải thích cho một loại báo cáo cụ thể hoặc tất cả.

        Args:
            report (QuickCheckReport): Đối tượng báo cáo QuickCheck đầy đủ.
            report_type (ExplainReportType): Loại báo cáo cần giải thích. 
                                             Mặc định là 'all'.

        Returns:
            str: Một chuỗi văn bản giải thích đã được định dạng.
        """
        if not isinstance(report, QuickCheckAnalysisReport):
            return "Invalid report format provided for explanation."

        # Sử dụng một danh sách để thu thập các phần giải thích
        explanation_parts = []

        # Logic phân nhánh dựa trên `report_type`
        if report_type in ['technical', 'all'] and report.technical_report:
            tech_summary = self.tech_explainer.explain(report.technical_report)
            explanation_parts.append(tech_summary)

        if report_type in ['forecasting', 'all'] and report.forecasting_report:
            forecasting_summary = self.forecasting_explainer.explain(report.forecasting_report)
            explanation_parts.append(forecasting_summary)
            
        if report_type in ['news', 'all'] and report.news_report:
            news_summary = self.news_explainer.explain(report.news_report)
            explanation_parts.append(news_summary)

        # Nếu không có phần nào được tạo (ví dụ: yêu cầu 'news' nhưng news_report là None)
        if not explanation_parts:
            return f"No data available to generate an explanation for '{report_type}'."

        # Nối tất cả các phần lại với nhau, cách nhau bằng hai dòng mới
        return "\n\n".join(explanation_parts)