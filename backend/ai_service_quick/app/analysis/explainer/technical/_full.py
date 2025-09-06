from typing import List, Dict, Any

# Import schema cấp cao nhất
from itapia_common.schemas.entities.analysis.technical import TechnicalReport

# Import các explainer chuyên biệt mà chúng ta đã xây dựng
from .daily import DailyAnalysisExplainer
from .intraday import IntradayAnalysisExplainer

class TechnicalAnalysisExplainer:
    """
    Generate a natural language summary for entire Technincal Report
    """
    _TEMPLATE = """
Technical Analysis Summary:

{daily_summary}

{intraday_summary}
    """.strip()

    def __init__(self):
        self.daily_explainer = DailyAnalysisExplainer()
        self.intraday_explainer = IntradayAnalysisExplainer()

    def explain(self, report: TechnicalReport) -> str:
        daily_summary = ""
        intraday_summary = ""

        # Decide which type of report contain in explanation
        
        if report.report_type in ['daily', 'all'] and report.daily_report:
            daily_summary = self.daily_explainer.explain(report.daily_report)
        
        if report.report_type in ['intraday', 'all'] and report.intraday_report:
            intraday_summary = self.intraday_explainer.explain(report.intraday_report)

        if not daily_summary and not intraday_summary:
            return "No technical analysis data is available to generate an explanation."

        return self._TEMPLATE.format(
            daily_summary=daily_summary,
            intraday_summary=intraday_summary
        ).strip()