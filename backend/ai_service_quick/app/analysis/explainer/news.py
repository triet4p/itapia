from typing import Dict, List, Optional

# Import các schema Pydantic tương ứng
from itapia_common.schemas.entities.analysis.news import (
    ImpactAssessmentReport,
    KeywordHighlightingReport,
    NERReport,
    NewsAnalysisReport,
    SentimentAnalysisReport,
    SingleNewsAnalysisReport,
)

# --- (Leaf Explainers) ---


class _SentimentExplainer:
    _TEMPLATE = "The overall sentiment is '{label}' with a confidence score of {score_pct:.0f}%."

    def explain(self, report: SentimentAnalysisReport) -> str:
        return self._TEMPLATE.format(label=report.label, score_pct=report.score * 100)


class _NERExplainer:
    _TEMPLATE = "Key entities mentioned include: {entities_str}."

    def _format_entities(self, report: NERReport) -> Optional[str]:
        if not report or not report.entities:
            return None

        # Group entities by type for better summarization
        entities_by_group: Dict[str, List[str]] = {}
        for entity in report.entities:
            group = entity.entity_group
            if group not in entities_by_group:
                entities_by_group[group] = []
            # Tránh thêm các thực thể trùng lặp
            if entity.word not in entities_by_group[group]:
                entities_by_group[group].append(entity.word)

        if not entities_by_group:
            return None

        # Prior important entities
        summary_parts = []
        if "ORG" in entities_by_group:
            orgs = ", ".join(entities_by_group["ORG"][:3])  # Lấy tối đa 3 tổ chức
            summary_parts.append(f"Organizations ({orgs})")
        if "PERSON" in entities_by_group:
            persons = ", ".join(entities_by_group["PERSON"][:2])  # Lấy tối đa 2 người
            summary_parts.append(f"Persons ({persons})")
        if "MONEY" in entities_by_group:
            persons = ", ".join(entities_by_group["MONEY"][:2])  # Lấy tối đa 2 money
            summary_parts.append(f"Moneys ({persons})")
        if "PRODUCT" in entities_by_group:
            persons = ", ".join(entities_by_group["PRODUCT"][:2])  # Lấy tối đa 2 người
            summary_parts.append(f"Products ({persons})")

        return " and ".join(summary_parts) if summary_parts else None

    def explain(self, report: Optional[NERReport]) -> str:
        entities_str = self._format_entities(report)
        if not entities_str:
            return "No key entities were identified."
        return self._TEMPLATE.format(entities_str=entities_str)


class _ImpactExplainer:
    _TEMPLATE = "The news is assessed to have '{level}' impact"
    _EVIDENCE_TEMPLATE = ", based on keywords such as '{keywords_str}'."

    def explain(self, report: ImpactAssessmentReport) -> str:
        if report.level == "unknown":
            return "The impact of this news is currently unknown."

        explanation = self._TEMPLATE.format(level=report.level)
        if report.words:
            keywords_str = ", ".join(report.words[:3])  # Lấy tối đa 3 từ khóa
            explanation += self._EVIDENCE_TEMPLATE.format(keywords_str=keywords_str)

        return explanation + "."


class _EvidenceExplainer:
    _TEMPLATE = "Key sentiment drivers include positive words like '{positive_str}' and negative words like '{negative_str}'."

    def explain(self, report: KeywordHighlightingReport) -> str:
        if not report or (
            not report.positive_keywords and not report.negative_keywords
        ):
            return ""

        positive_str = (
            ", ".join(report.positive_keywords[:3])
            if report.positive_keywords
            else "none"
        )
        negative_str = (
            ", ".join(report.negative_keywords[:3])
            if report.negative_keywords
            else "none"
        )

        return self._TEMPLATE.format(
            positive_str=positive_str, negative_str=negative_str
        )


# --- Explainer Cấp Trung Gian (Composite Explainers) ---


class _SingleNewsExplainer:
    _TEMPLATE = "For the news titled '{title}', the analysis is as follows: {sentiment_exp} {impact_exp} {ner_exp} {evidence_exp}"

    def __init__(self):
        self.sentiment_explainer = _SentimentExplainer()
        self.ner_explainer = _NERExplainer()
        self.impact_explainer = _ImpactExplainer()
        self.evidence_explainer = _EvidenceExplainer()

    def explain(self, report: SingleNewsAnalysisReport) -> str:
        title = " ".join(report.text.split()[:20]) + "..."
        title = title.capitalize()

        sentiment_exp = self.sentiment_explainer.explain(report.sentiment_analysis)
        impact_exp = (
            self.impact_explainer.explain(report.impact_assessment)
            if report.impact_assessment
            else ""
        )
        ner_exp = self.ner_explainer.explain(report.ner) if report.ner else ""
        evidence_exp = (
            self.evidence_explainer.explain(report.keyword_highlighting_evidence)
            if report.keyword_highlighting_evidence
            else ""
        )

        # Nối các phần lại với nhau, loại bỏ các khoảng trắng thừa
        full_explanation = " ".join(
            filter(None, [sentiment_exp, impact_exp, ner_exp, evidence_exp])
        )

        return f'"{title}": {full_explanation}'


# --- Explainer Cấp Cao Nhất ---


class NewsAnalysisExplainer:
    _HEADER = "News Analysis Summary:"
    _NO_NEWS = "No recent news available for analysis."

    def __init__(self):
        self.single_news_explainer = _SingleNewsExplainer()

    def explain(self, report: NewsAnalysisReport) -> str:
        if not report or not report.reports:
            return self._NO_NEWS

        def sort_key(r: SingleNewsAnalysisReport):
            impact_order = {"high": 0, "moderate": 1, "low": 2, "unknown": 3}
            impact = impact_order.get(r.impact_assessment.level, 3)
            sentiment_score = abs(r.sentiment_analysis.score - 0.5)
            return (impact, -sentiment_score)

        sorted_reports = sorted(report.reports, key=sort_key)

        summaries = [self.single_news_explainer.explain(r) for r in sorted_reports[:3]]

        # Tạo một bản tóm tắt tổng thể
        num_reports = len(report.reports)
        num_positive = sum(
            1 for r in report.reports if r.sentiment_analysis.label == "positive"
        )
        num_high_impact = sum(
            1
            for r in report.reports
            if r.impact_assessment and r.impact_assessment.level == "high"
        )

        overall_summary = (
            f"Overall, an analysis of {num_reports} recent news items found {num_positive} positive stories. "
            f"Notably, {num_high_impact} items were assessed as having high market impact."
        )

        return (
            f"{self._HEADER}\n{overall_summary}\n\nKey Highlights:\n- "
            + "\n- ".join(summaries)
        )
