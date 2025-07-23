from typing import List
import shap
import pandas as pd
from sklearn.multioutput import MultiOutputRegressor
from app.forecasting.model import ForecastingModel

from itapia_common.dblib.schemas.reports.forecasting import TopFeature, BaseSHAPExplaination, SHAPExplaination

from abc import ABC, abstractmethod

class SHAPExplainer(ABC):
    def __init__(self, model: ForecastingModel):
        if model.kernel_model is None:
            raise ValueError("Kernel model has not been loaded")
        self.model = model
        self.task = model.task
    
    @abstractmethod
    def explain_prediction(self, X_instance: pd.DataFrame) -> List[SHAPExplaination]:
        pass
    
    def _format_shap_explanation(self, shap_values_array, X_instance: pd.DataFrame, top_n=5,
                                 base_value: int = 0) -> BaseSHAPExplaination:
        """Hàm tiện ích để định dạng output của SHAP."""
        feature_names = X_instance.columns
        feature_values = X_instance.iloc[0].values
        
        # Tạo DataFrame từ SHAP values
        shap_df = pd.DataFrame({
            'feature': feature_names,
            'value': feature_values,
            'shap_value': shap_values_array.flatten()
        })
        
        # Sắp xếp theo giá trị tuyệt đối của SHAP value
        shap_df['abs_shap'] = shap_df['shap_value'].abs()
        top_features = shap_df.sort_values(by='abs_shap', ascending=False).head(top_n)
        prediction_outcome = base_value + shap_df['shap_value'].sum()
        # Tạo output có cấu trúc
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
    """Explainer cho các mô hình cây đơn mục tiêu (phân loại)."""
    def __init__(self, model: ForecastingModel):
        super().__init__(model)
        if self.task.task_type != 'clf':
            raise TypeError("TreeSHAPExplainer is intended for classification tasks.")
        if not hasattr(self.model.kernel_model, 'classes_'):
            raise TypeError("Model for TreeSHAPExplainer must have a 'classes_' attribute.")

        self.explainer = shap.TreeExplainer(self.model.kernel_model)
        self.class_map = {label: i for i, label in enumerate(self.model.kernel_model.classes_)}
        
    def explain_prediction(self, X_instance: pd.DataFrame) -> List[SHAPExplaination]:
        shap_values_3d = self.explainer.shap_values(X_instance)
        prediction = self.model.predict(X_instance)[0]
        
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
    Explainer chuyên dụng cho các mô hình cây đa mục tiêu, được bọc bởi
    sklearn.multioutput.MultiOutputRegressor.
    """
    def __init__(self, model: ForecastingModel):
        super().__init__(model)
        if self.task.task_type != 'reg':
            raise TypeError("MultiOutputTreeSHAPExplainer is intended for regression tasks.")
        if not isinstance(self.model.kernel_model, MultiOutputRegressor):
            raise TypeError("The kernel model must be an instance of MultiOutputRegressor.")

        # Tạo một dictionary chứa các TreeExplainer, mỗi cái cho một model con (estimator)
        self.explainers = {
            target_name: shap.TreeExplainer(estimator)
            for target_name, estimator in zip(self.task.targets, self.model.kernel_model.estimators_)
        }

    def explain_prediction(self, X_instance: pd.DataFrame) -> List[SHAPExplaination]:
        """
        Tạo giải thích cho TẤT CẢ các mục tiêu đầu ra và trả về một dictionary
        chứa các giải thích riêng biệt.
        """
        full_explanation = []

        # Lặp qua từng explainer đã được tạo cho mỗi mục tiêu
        for target_name, explainer in self.explainers.items():
            # shap_values ở đây sẽ có shape (1, num_features) vì mỗi model con là single-output
            shap_values_for_output = explainer.shap_values(X_instance)
            base_value_for_output = explainer.expected_value
            
            # Định dạng lời giải thích cho mục tiêu này
            explanation = self._format_shap_explanation(
                shap_values_for_output.flatten(), # làm phẳng thành 1D array
                X_instance,
                base_value=base_value_for_output,
                top_n=5 # Có thể dùng top_n nhỏ hơn cho mỗi output
            )
            
            # Lấy tên ngắn gọn của target (ví dụ: 'mean_5d' từ 'target_mean_5d')
            short_target_name = '_'.join(target_name.split('_')[1:])
            full_explanation.append(SHAPExplaination(
                for_target=short_target_name,
                explaination=explanation
            ))
            
        return full_explanation
        
