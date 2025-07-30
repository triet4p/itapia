from typing import List, Dict, Any

# Import các schema Pydantic tương ứng từ thư viện chung
from itapia_common.schemas.entities.reports.technical.daily import (
    DailyAnalysisReport,
    KeyIndicators,
    TrendReport,
    MidTermTrendReport,
    LongTermTrendReport,
    OverallStrengthTrendReport,
    SRReport,
    SRIdentifyLevelObj,
    PatternReport,
    PatternObj
)

# --- Explainer Cấp Thấp Nhất (Leaf Explainers) ---

class _KeyIndicatorsExplainer:
    _TEMPLATE = "Key indicators show an RSI(14) of {rsi_14:.2f}. The price is currently trading between the Bollinger Bands® at {bbl_20:.2f} (lower) and {bbu_20:.2f} (upper)."

    def explain(self, indicators: KeyIndicators) -> str:
        # Kiểm tra xem các giá trị cần thiết có tồn tại không
        if indicators.rsi_14 is None or indicators.bbl_20 is None or indicators.bbu_20 is None:
            return "Key indicator data is incomplete for a full explanation."
        
        return self._TEMPLATE.format(
            rsi_14=indicators.rsi_14,
            bbl_20=indicators.bbl_20,
            bbu_20=indicators.bbu_20
        )

class _MidTermTrendExplainer:
    _TEMPLATE = "In the mid-term, the trend is identified as an '{ma_direction}' based on moving averages. The ADX indicator also suggests an '{adx_direction}'."

    def explain(self, report: MidTermTrendReport) -> str:
        return self._TEMPLATE.format(
            ma_direction=report.ma_direction,
            adx_direction=report.adx_direction
        )

class _LongTermTrendExplainer:
    _TEMPLATE = "The long-term outlook, based on slower moving averages, indicates a '{ma_direction}'."

    def explain(self, report: LongTermTrendReport) -> str:
        return self._TEMPLATE.format(ma_direction=report.ma_direction)

class _OverallStrengthTrendExplainer:
    _TEMPLATE = "Overall, the trend strength is considered '{strength}' with a calculated value of {value}."

    def explain(self, report: OverallStrengthTrendReport) -> str:
        return self._TEMPLATE.format(
            strength=report.strength,
            value=report.value
        )

class _SRExplainer:
    _TEMPLATE = "Key support levels are identified near {supports_str}. Key resistance levels are found near {resistances_str}."
    
    def _format_levels(self, levels: List[SRIdentifyLevelObj]) -> str:
        if not levels:
            return "no significant levels"
        # Chỉ lấy 2 mức quan trọng nhất để câu văn gọn gàng
        level_values = [f"{lvl.level:.2f}" for lvl in levels[:2]]
        return " and ".join(level_values)

    def explain(self, report: SRReport) -> str:
        supports_str = self._format_levels(report.supports)
        resistances_str = self._format_levels(report.resistances)

        return self._TEMPLATE.format(
            supports_str=supports_str,
            resistances_str=resistances_str
        )

class _PatternExplainer:
    _TEMPLATE = "Recent price action has formed several patterns. The most notable are: {patterns_summary}"
    
    def _build_patterns_summary(self, patterns: List[PatternObj]) -> str:
        if not patterns:
            return "no significant patterns identified."
        
        summaries = []
        # Chỉ giải thích 2 mẫu hình quan trọng nhất
        for pattern in patterns[:2]:
            sentiment_text = "a bullish" if pattern.sentiment == 'bull' else "a bearish"
            summaries.append(f"{sentiment_text} '{pattern.name}' ({pattern.pattern_type}) pattern")
        
        return ", ".join(summaries) + "."

    def explain(self, report: PatternReport) -> str:
        patterns_summary = self._build_patterns_summary(report.top_patterns)
        
        return self._TEMPLATE.format(patterns_summary=patterns_summary)

# --- Explainer Cấp Trung Gian (Composite Explainers) ---

class _TrendExplainer:
    _TEMPLATE = "{mid_term_exp} {long_term_exp} {strength_exp}"

    def __init__(self):
        self.mid_term_explainer = _MidTermTrendExplainer()
        self.long_term_explainer = _LongTermTrendExplainer()
        self.strength_explainer = _OverallStrengthTrendExplainer()

    def explain(self, report: TrendReport) -> str:
        mid_term_exp = self.mid_term_explainer.explain(report.midterm_report)
        long_term_exp = self.long_term_explainer.explain(report.longterm_report)
        strength_exp = self.strength_explainer.explain(report.overall_strength)
        
        return self._TEMPLATE.format(
            mid_term_exp=mid_term_exp,
            long_term_exp=long_term_exp,
            strength_exp=strength_exp
        )

# --- Explainer Cấp Cao Nhất (Main Explainer for this file) ---

class DailyAnalysisExplainer:
    """
    Tạo ra một bản tóm tắt bằng ngôn ngữ tự nhiên cho toàn bộ DailyAnalysisReport.
    """
    _TEMPLATE = "Daily Technical Analysis Summary:\n{key_indicators_exp}\n{trend_exp}\n{sr_exp}\n{pattern_exp}"

    def __init__(self):
        # Khởi tạo tất cả các sub-explainer cần thiết
        self.key_indicators_explainer = _KeyIndicatorsExplainer()
        self.trend_explainer = _TrendExplainer()
        self.sr_explainer = _SRExplainer()
        self.pattern_explainer = _PatternExplainer()

    def explain(self, report: DailyAnalysisReport) -> str:
        """
        Tạo ra một đoạn văn giải thích hoàn chỉnh.

        Args:
            report (DailyAnalysisReport): Đối tượng báo cáo Pydantic.

        Returns:
            str: Một chuỗi văn bản giải thích.
        """
        key_indicators_exp = self.key_indicators_explainer.explain(report.key_indicators)
        trend_exp = self.trend_explainer.explain(report.trend_report)
        sr_exp = self.sr_explainer.explain(report.sr_report)
        pattern_exp = self.pattern_explainer.explain(report.pattern_report)

        return self._TEMPLATE.format(
            key_indicators_exp=key_indicators_exp,
            trend_exp=trend_exp,
            sr_exp=sr_exp,
            pattern_exp=pattern_exp
        ).strip()