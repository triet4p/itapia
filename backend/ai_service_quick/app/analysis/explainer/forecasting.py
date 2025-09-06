from typing import Union, List, Dict
from itapia_common.schemas.entities.analysis.forecasting import (
    ForecastingReport, SingleTaskForecastReport, 
    TripleBarrierTaskMetadata, NDaysDistributionTaskMetadata,
    SHAPExplaination, TopFeature
)

# Mapping to translate technical name to friendly name

PROBLEM_ID_TO_NAME = {
    "triple-barrier": "Triple Barrier Classification",
    "ndays-distribution": "Price Distribution Regression"
}

DISTRIBUTION_TARGET_TO_NAME = {
    "mean": "average price change",
    "std": "price volatility (standard deviation)",
    "min": "minimum price change",
    "max": "maximum price change",
    "q25": "25th percentile price change",
    "q75": "75th percentile price change"
}

# --- SHAP EXPLAINER (giữ nguyên, đã rất tốt) ---
class _SHAPExplainer:
    _TEMPLATE = "The model's final prediction for {target_name} is {prediction_outcome:.2f}{unit_symbol}, starting from a base average of {base_value:.2f}{unit_symbol}. The most significant factor was '{top_feature_name}', which had a {top_feature_effect} impact."
    _MULTI_FEATURE_TEMPLATE = " The top factors were: {feature_list}."

    def _format_feature_list(self, features: List[TopFeature]) -> str:
        descriptions = [f"'{f.feature}' (a {f.effect} factor)" for f in features[:2]] # Lấy 2 features hàng đầu
        return ", ".join(descriptions)

    def explain(self, evidence: SHAPExplaination, unit: str) -> str:
        expl = evidence.explaination
        unit_symbol = "%" if unit == "percent" else ""
        
        if not expl.top_features:
            return f"The model's final prediction for {evidence.for_target} is {expl.prediction_outcome:.2f}{unit_symbol}."
            
        top_feature = expl.top_features[0]
        
        base_explanation = self._TEMPLATE.format(
            target_name=evidence.for_target,
            prediction_outcome=expl.prediction_outcome,
            unit_symbol=unit_symbol,
            base_value=expl.base_value,
            top_feature_name=top_feature.feature,
            top_feature_effect=top_feature.effect
        )

        if len(expl.top_features) > 1:
            base_explanation += self._MULTI_FEATURE_TEMPLATE.format(
                feature_list=self._format_feature_list(expl.top_features)
            )

        return base_explanation

# --- SINGLE TASK EXPLAINER ---
class _SingleTaskForecastExplainer:
    def __init__(self):
        self.shap_explainer = _SHAPExplainer()

    def _explain_triple_barrier(self, report: SingleTaskForecastReport) -> str:
        metadata: TripleBarrierTaskMetadata = report.task_metadata
        
        prediction_label = report.prediction[0]
        
        # Mapping
        prediction_text_map = {
            1: "a 'Win' (price increase)",
            -1: "a 'Loss' (price decrease)",
            0: "a 'Timeout' (no significant move)"
        }
        prediction_text = prediction_text_map.get(prediction_label, "an unknown outcome")

        task_intro = (
            f"For the '{PROBLEM_ID_TO_NAME.get(metadata.problem_id)}' task over a {metadata.horizon}-day horizon, "
            f"the model predicts the most likely outcome is {prediction_text}. "
            f"This is based on a profit target of {metadata.tp_pct*100:.1f}% and a stop-loss of {metadata.sl_pct*100:.1f}%."
        )
        
        evidence_to_explain = report.evidence[0] if report.evidence else None

        evidence_text = ""
        if evidence_to_explain:
            evidence_text = " " + self.shap_explainer.explain(evidence_to_explain, report.units)

        return task_intro + evidence_text

    def _explain_distribution(self, report: SingleTaskForecastReport) -> str:
        metadata: NDaysDistributionTaskMetadata = report.task_metadata
        
        task_intro = (
            f"For the {metadata.horizon}-day '{PROBLEM_ID_TO_NAME.get(metadata.problem_id)}' task, "
            "the model forecasts the following percentage price changes:"
        )

        # Create a dictionary to easily look up predictions by target name
        prediction_map = {ev.for_target.split('_')[0]: pred_val for ev, pred_val in zip(report.evidence, report.prediction)}
        
        mean_change = prediction_map.get('mean')
        q25 = prediction_map.get('q25')
        q75 = prediction_map.get('q75')
        
        summary_lines = []
        if mean_change is not None:
            summary_lines.append(f"- An average change of {mean_change:.2f}%.")
        if q25 is not None and q75 is not None:
            summary_lines.append(f"- A likely 50% range of outcomes between {q25:.2f}% and {q75:.2f}%.")
            
        # Tìm bằng chứng cho dự báo quan trọng nhất (mean)
        mean_evidence = next((ev for ev in report.evidence if ev.for_target.startswith("mean")), None)
        evidence_text = ""
        if mean_evidence and mean_evidence.explaination.top_features:
            top_feature = mean_evidence.explaination.top_features[0]
            evidence_text = f" The forecast for the average change was primarily driven by the '{top_feature.feature}' feature."
        
        return f"{task_intro}\n" + "\n".join(summary_lines) + evidence_text

    def explain(self, report: SingleTaskForecastReport) -> str:
        if isinstance(report.task_metadata, TripleBarrierTaskMetadata):
            return self._explain_triple_barrier(report)
        elif isinstance(report.task_metadata, NDaysDistributionTaskMetadata):
            return self._explain_distribution(report)
        else:
            return f"An explanation for task '{report.task_name}' is not available."

class ForecastingExplainer:
    _HEADER = "Forecasting Analysis Summary:"

    def __init__(self):
        self.single_task_explainer = _SingleTaskForecastExplainer()

    def explain(self, report: ForecastingReport) -> str:
        if not report or not report.forecasts:
            return "No forecasting analysis is available."
        
        # Tạo một đoạn tóm tắt cho mỗi task và nối chúng lại
        summaries = [self.single_task_explainer.explain(task_report) for task_report in report.forecasts]
        
        return f"{self._HEADER}\n\n" + "\n\n".join(summaries)