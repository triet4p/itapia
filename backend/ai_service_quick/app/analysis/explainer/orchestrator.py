from typing import Literal, Union

from itapia_common.schemas.entities.analysis import QuickCheckAnalysisReport

from .technical import TechnicalAnalysisExplainer
from .news import NewsAnalysisExplainer
from .forecasting import ForecastingExplainer

ExplainReportType = Literal['technical', 'news', 'forecasting', 'all']

class AnalysisExplainerOrchestrator:
    """
    Orchestrate the generation of natural language summaries for
    different parts of Quick Check Report.
    """
    def __init__(self):
        self.tech_explainer = TechnicalAnalysisExplainer()
        self.news_explainer = NewsAnalysisExplainer()
        self.forecasting_explainer = ForecastingExplainer()

    def explain(self, 
                report: QuickCheckAnalysisReport, 
                report_type: ExplainReportType = 'all'
               ) -> str:
        """
        Create a natural language explanation for a report, with require type

        Args:
            report (QuickCheckReport): Report object.
            report_type (ExplainReportType): Type of sub-report to explain, defaults to 'all'

        Returns:
            str: A plain text explanation
        """
        if not isinstance(report, QuickCheckAnalysisReport):
            return "Invalid report format provided for explanation."

        explanation_parts = []

        # Branch based on report_type paramaters.
        if report_type in ['technical', 'all'] and report.technical_report:
            tech_summary = self.tech_explainer.explain(report.technical_report)
            explanation_parts.append(tech_summary)

        if report_type in ['forecasting', 'all'] and report.forecasting_report:
            forecasting_summary = self.forecasting_explainer.explain(report.forecasting_report)
            explanation_parts.append(forecasting_summary)
            
        if report_type in ['news', 'all'] and report.news_report:
            news_summary = self.news_explainer.explain(report.news_report)
            explanation_parts.append(news_summary)

        if not explanation_parts:
            return f"No data available to generate an explanation for '{report_type}'."

        return "\n\n".join(explanation_parts)