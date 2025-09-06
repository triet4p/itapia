from itapia_common.schemas.entities.analysis.technical.intraday import (
    IntradayAnalysisReport,
    CurrentStatusReport,
    KeyLevelsReport,
    MomentumReport
)

# --- (Leaf Explainers) ---

class _CurrentStatusExplainer:
    _TEMPLATE = "Currently, the price is trading '{open_status}' the opening price. Compared to the Volume-Weighted Average Price (VWAP), it is '{vwap_status}'. The short-term RSI suggests the stock is in a '{rsi_status}' state."

    def explain(self, report: CurrentStatusReport) -> str:
        # Replace "undefined" with a friendlier phrase.
        vwap_status_text = "at an undefined level" if report.vwap_status == 'undefined' else report.vwap_status
        
        return self._TEMPLATE.format(
            open_status=report.open_status,
            vwap_status=vwap_status_text,
            rsi_status=report.rsi_status
        )

class _KeyLevelsExplainer:
    _TEMPLATE = "Key intraday levels to watch are the day's high at {day_high:.2f}, the day's low at {day_low:.2f}, and the VWAP at {vwap:.2f}."

    def explain(self, report: KeyLevelsReport) -> str:
        if report.vwap is None:
            return f"Key intraday levels are the day's high at {report.day_high:.2f} and the day's low at {report.day_low:.2f}."
            
        return self._TEMPLATE.format(
            day_high=report.day_high,
            day_low=report.day_low,
            vwap=report.vwap
        )

class _MomentumExplainer:
    _TEMPLATE = "Momentum analysis shows a '{macd_crossover_text}' signal from the MACD. Volume is currently '{volume_status}'{breakout_text}."
    
    def _format_breakout_text(self, or_status: str) -> str:
        if or_status == 'bull-breakout':
            return ", with a bullish breakout above the opening range"
        elif or_status == 'bear-breakdown':
            return ", with a bearish breakdown below the opening range"
        else: # 'inside'
            return ", and the price remains inside the opening range"

    def explain(self, report: MomentumReport) -> str:
        macd_crossover_text = "neutral"
        if report.macd_crossover == 'bull':
            macd_crossover_text = "bullish crossover"
        elif report.macd_crossover == 'bear':
            macd_crossover_text = "bearish crossover"
            
        breakout_text = self._format_breakout_text(report.opening_range_status)
        
        return self._TEMPLATE.format(
            macd_crossover_text=macd_crossover_text,
            volume_status=report.volume_status,
            breakout_text=breakout_text
        )

# --- Explainer Cấp Cao Nhất (Main Explainer for this file) ---

class IntradayAnalysisExplainer:
    """
    Tạo ra một bản tóm tắt bằng ngôn ngữ tự nhiên cho toàn bộ IntradayAnalysisReport.
    """
    _TEMPLATE = "Intraday Analysis Summary:\n{status_exp}\n{momentum_exp}\n{levels_exp}"

    def __init__(self):
        # Khởi tạo tất cả các sub-explainer cần thiết
        self.status_explainer = _CurrentStatusExplainer()
        self.momentum_explainer = _MomentumExplainer()
        self.levels_explainer = _KeyLevelsExplainer()

    def explain(self, report: IntradayAnalysisReport) -> str:
        if report is None:
            return "No intraday analysis is available."

        status_exp = self.status_explainer.explain(report.current_status_report)
        momentum_exp = self.momentum_explainer.explain(report.momentum_report)
        levels_exp = self.levels_explainer.explain(report.key_levels)

        return self._TEMPLATE.format(
            status_exp=status_exp,
            momentum_exp=momentum_exp,
            levels_exp=levels_exp
        ).strip()