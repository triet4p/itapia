from typing import List
import shap
import pandas as pd
from sklearn.multioutput import MultiOutputRegressor
from .model import ForecastingModel

from itapia_common.schemas.entities.analysis.forecasting import TopFeature, BaseSHAPExplaination, SHAPExplaination

from abc import ABC, abstractmethod

class SHAPExplainer(ABC):
    def __init__(self, model: ForecastingModel,
                 snapshot_id: str|None = None):
        if model.kernel_model is None:
            raise ValueError("Kernel model has not been loaded")
        self.model = model
        self.task = model.task
        
        if snapshot_id is None:
            self._to_explain_kernel = self.model.kernel_model
        else:
            self._to_explain_kernel = self.model.snapshot_models[snapshot_id]
    
    @abstractmethod
    def explain_prediction(self, X_instance: pd.DataFrame) -> List[SHAPExplaination]:
        """Explain a prediction using SHAP values."""
        pass
    
    def _format_shap_explanation(self, shap_values_array, X_instance: pd.DataFrame, top_n=5,
                                 base_value: int = 0) -> BaseSHAPExplaination:
        feature_names = X_instance.columns
        feature_values = X_instance.iloc[0].values
        
        # Create DF from SHAP Values
        shap_df = pd.DataFrame({
            'feature': feature_names,
            'value': feature_values,
            'shap_value': shap_values_array.flatten()
        })
        
        shap_df['abs_shap'] = shap_df['shap_value'].abs()
        top_features = shap_df.sort_values(by='abs_shap', ascending=False).head(top_n)
        prediction_outcome = base_value + shap_df['shap_value'].sum()

        # Create structure output        
        explanation = BaseSHAPExplaination(
            base_value=round(base_value, 4),
            prediction_outcome=round(prediction_outcome, 4),
            top_features=[
                TopFeature(
                    feature=row['feature'],
                    value=round(row['value'], 4),
                    contribution=round(row['shap_value'], 4),
                    effect="positive" if row['shap_value'] > 0 else "negative"
                )
                for _, row in top_features.iterrows()
            ]
        )
        return explanation
    
class TreeSHAPExplainer(SHAPExplainer):
    """Explainer for tree-based classification model (single-output)."""
    def __init__(self, model: ForecastingModel, snapshot_id: str|None=None):
        super().__init__(model, snapshot_id)
        if self.task.task_type != 'clf':
            raise TypeError("TreeSHAPExplainer is intended for classification tasks.")
        if not hasattr(self._to_explain_kernel, 'classes_'):
            raise TypeError("Model for TreeSHAPExplainer must have a 'classes_' attribute.")

        self.explainer = shap.TreeExplainer(self._to_explain_kernel)
        self.class_map = {label: i for i, label in enumerate(self._to_explain_kernel.classes_)}
        
    def explain_prediction(self, X_instance: pd.DataFrame) -> List[SHAPExplaination]:
        shap_values_3d = self.explainer.shap_values(X_instance)
        prediction = self.model.predict_kernel_model(self._to_explain_kernel, X_instance)[0]
        
        predicted_class_index = self.class_map[prediction]
        shap_values_for_prediction = shap_values_3d[0, :, predicted_class_index]
        base_value_for_prediction = self.explainer.expected_value[predicted_class_index]
        
        explaination = self._format_shap_explanation(
            shap_values_for_prediction, X_instance,
            base_value=base_value_for_prediction,
            top_n=8
        )
        
        short_target_name = '_'.join(self.task.targets[0].split('_')[1:])
        
        return [SHAPExplaination(
            for_target=short_target_name,
            explaination=explaination
        )]
        
class MultiOutputTreeSHAPExplainer(SHAPExplainer):
    """
    Explainer for tree-based multi output model.
    """
    def __init__(self, model: ForecastingModel, snapshot_id: str|None = None):
        super().__init__(model, snapshot_id)
        if self.task.task_type != 'reg':
            raise TypeError("MultiOutputTreeSHAPExplainer is intended for regression tasks.")
        if not isinstance(self._to_explain_kernel, MultiOutputRegressor):
            raise TypeError("The kernel model must be an instance of MultiOutputRegressor.")

        self.explainers = {
            target_name: shap.TreeExplainer(estimator)
            for target_name, estimator in zip(self.task.targets, self._to_explain_kernel.estimators_)
        }

    def explain_prediction(self, X_instance: pd.DataFrame) -> List[SHAPExplaination]:
        full_explanation = []

        for target_name, explainer in self.explainers.items():
            # shap_values shape is (1, num_features)
            shap_values_for_output = explainer.shap_values(X_instance)
            base_value_for_output = explainer.expected_value
            
            explanation = self._format_shap_explanation(
                shap_values_for_output.flatten(), # làm phẳng thành 1D array
                X_instance,
                base_value=base_value_for_output,
                top_n=5 # Có thể dùng top_n nhỏ hơn cho mỗi output
            )
            
            # Get short target name, for example target_mean_5d is mean_5d
            short_target_name = '_'.join(target_name.split('_')[1:])
            full_explanation.append(SHAPExplaination(
                for_target=short_target_name,
                explaination=explanation
            ))
            
        return full_explanation
        
