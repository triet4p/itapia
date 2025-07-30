from typing import List
from itapia_common.schemas.entities.reports.news import SingleNewsAnalysisReport, SummaryReport

class ResultSummarizer:
    def summary(self, reports: List[SingleNewsAnalysisReport]):
        if len(reports) == 0:
            return SummaryReport(
                num_positive_sentiment=0,
                num_negative_sentiment=0,
                num_high_impact=0,
                num_moderate_impact=0,
                num_low_impact=0,
                avg_of_positive_keyword_found=0.0,
                avg_of_negative_keyword_found=0.0,
                avg_of_ner_found=0.0
            )
        num_positive_sentiment = sum(1 for report in reports if report.sentiment_analysis.label == 'positive')
        num_negative_sentiment = sum(1 for report in reports if report.sentiment_analysis.label == 'negative')
        
        num_high_impact = sum(1 for report in reports if report.impact_assessment.level == 'high')
        num_moderate_impact = sum(1 for report in reports if report.impact_assessment.level == 'moderate')
        num_low_impact = sum(1 for report in reports if report.impact_assessment.level == 'low')
        
        avg_of_positive_keyword_found = sum(len(report.keyword_highlighting_evidence.positive_keywords) for report in reports) / len(reports)
        avg_of_negative_keyword_found = sum(len(report.keyword_highlighting_evidence.negative_keywords) for report in reports) / len(reports)
        
        avg_of_ner_found = sum(len(report.ner.entities) for report in reports) / len(reports)
        
        return SummaryReport(
            num_positive_sentiment=num_positive_sentiment,
            num_negative_sentiment=num_negative_sentiment,
            num_high_impact=num_high_impact,
            num_moderate_impact=num_moderate_impact,
            num_low_impact=num_low_impact,
            avg_of_positive_keyword_found=avg_of_positive_keyword_found,
            avg_of_negative_keyword_found=avg_of_negative_keyword_found,
            avg_of_ner_found=avg_of_ner_found
        )