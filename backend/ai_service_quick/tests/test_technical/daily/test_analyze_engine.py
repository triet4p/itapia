# tests/test_technical/test_analysis_engine.daily.py

import pytest
import pandas as pd
import numpy as np

# Import lớp chính và các lớp con để có thể mock nếu cần
from app.analysis.technical.analysis_engine.daily import DailyAnalysisEngine
from app.analysis.technical.analysis_engine.daily.trend_analyzer import DailyTrendAnalyzer
from app.analysis.technical.analysis_engine.daily.sr_identifier import DailySRIdentifier
from app.analysis.technical.analysis_engine.daily.pattern_recognizer import DailyPatternRecognizer

# Sử dụng lại hàm helper từ test_pattern_recognizer
from .test_pattern_recoginzer import create_pattern_df

def test_analysis_engine_integration():
    """
    Test tích hợp: Kiểm tra xem AnalysisEngine có gọi đúng các module con
    và tạo ra một báo cáo có cấu trúc đúng hay không.
    """
    # Tạo một DataFrame giả lập có mẫu hình Double Bottom
    price_seq = [110, 95, 90, 100, 92, 90, 102]
    # Thêm dữ liệu nến
    cdl_data = {'cdl_hammer': 100}
    # Thêm dữ liệu chỉ báo giả lập cho dòng cuối
    indicator_data = {
        'SMA_20': 95.0, 'SMA_50': 92.0, 'SMA_200': 100.0,
        'RSI_14': 60.0, 'ADX_14': 25.0, 'DMP_14': 30.0, 'DMN_14': 15.0,
        'BBU_20_2.0': 105.0, 'BBL_20_2.0': 85.0, 'ATR_14': 2.5
    }
    
    df = create_pattern_df(price_seq, cdl_data)
    # Cập nhật dòng cuối cùng với dữ liệu chỉ báo chính xác
    for key, value in indicator_data.items():
        df.loc[df.index[-1], key] = value

    # Khởi tạo Engine
    engine = DailyAnalysisEngine(df, history_window=7, distance=1, prominence_pct=0.01)
    
    # Lấy báo cáo
    report = engine.get_analysis_report()
    
    # --- Kiểm tra cấu trúc và nội dung ---
    
    # 1. Kiểm tra các key chính
    assert "indicators" in report
    assert "trend" in report
    assert "support_resistance" in report
    assert "patterns" in report
    
    # 2. Kiểm tra kết quả từ TrendAnalyzer
    assert report["trend"]["medium_term"]["direction"] == "Uptrend"
    
    # 3. Kiểm tra kết quả từ SupportResistanceIdentifier
    assert isinstance(report["support_resistance"]["support"], list)
    assert isinstance(report["support_resistance"]["resistance"], list)
    
    # 4. Kiểm tra kết quả từ PatternRecognizer
    pattern_names = [p['sentiment'] + ' ' + p['pattern_name'] for p in report["patterns"]]
    assert "Bullish Double Bottom" in pattern_names
    assert "Bullish Hammer" in pattern_names
    
    # 5. Kiểm tra kết quả từ _extract_key_indicators
    assert report["indicators"]["SMA_50"] == 92.0
    assert report["indicators"]["RSI_14"] == 60.0