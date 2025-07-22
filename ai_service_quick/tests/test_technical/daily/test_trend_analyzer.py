import pytest
import pandas as pd

# Import lớp cần test
from app.technical.analysis_engine.daily.trend_analyzer import DailyTrendAnalyzer

# --- Các bài test cho TrendAnalyzer ---

def test_long_term_uptrend():
    """Kiểm tra trường hợp xu hướng dài hạn tăng."""
    # Tạo dữ liệu giả lập cho dòng cuối cùng
    latest_row = pd.Series({
        'close': 150,
        'SMA_50': 140,
        'SMA_200': 120 # SMA_50 > SMA_200
    })
    # Chỉ cần dòng cuối để test, nhưng class cần DataFrame
    df = pd.DataFrame([latest_row], index=[pd.to_datetime("2025-01-01")])
    analyzer = DailyTrendAnalyzer(df)
    report = analyzer._get_long_term_view()
    
    assert report['direction'] == "Uptrend"
    assert "Above" in report['status']

def test_medium_term_downtrend_under_pressure():
    """Kiểm tra trường hợp xu hướng trung hạn giảm và chịu áp lực."""
    latest_row = pd.Series({
        'close': 130,
        'SMA_20': 135,
        'SMA_50': 145, # SMA_20 < SMA_50
        'DMP_14': 15,
        'DMN_14': 25   # DMN > DMP -> Hướng xuống
    })
    df = pd.DataFrame([latest_row], index=[pd.to_datetime("2025-01-01")])
    analyzer = DailyTrendAnalyzer(df)
    report = analyzer._get_mid_term_view()

    assert report['direction'] == "Downtrend"
    assert "Under Pressure" in report['status']
    assert report['adx_direction'] == "Down"

def test_adx_strength_analysis():
    """Kiểm tra logic phân loại sức mạnh xu hướng của ADX."""
    analyzer = DailyTrendAnalyzer(pd.DataFrame([{'ADX_14': -1}], index=[pd.to_datetime("2025-01-01")])) # Khởi tạo tạm
    
    # Test Strong
    analyzer.latest_row = pd.Series({'ADX_14': 30})
    assert analyzer._get_adx_strength('ADX_14').get('strength') == "Strong"
    
    # Test Moderate
    analyzer.latest_row = pd.Series({'ADX_14': 22})
    assert analyzer._get_adx_strength('ADX_14').get('strength') == "Moderate"
    
    # Test Weak
    analyzer.latest_row = pd.Series({'ADX_14': 15})
    assert analyzer._get_adx_strength('ADX_14').get('strength') == "Weak"

def test_full_analysis_report_structure():
    """Kiểm tra cấu trúc của báo cáo tổng hợp cuối cùng."""
    # Tạo dữ liệu giả lập có đủ các cột cần thiết
    data = {
        'close': 160,
        'SMA_10': 155, 'SMA_20': 150, 'SMA_50': 140, 'SMA_200': 120,
        'ADX_14': 28, 'DMP_14': 30, 'DMN_14': 15
    }
    df = pd.DataFrame([data], index=[pd.to_datetime("2025-01-01")])
    analyzer = DailyTrendAnalyzer(df)
    report = analyzer.analyze_trend()

    # Kiểm tra các key cấp cao nhất
    assert "primary_focus" in report
    assert "long_term" in report
    assert "medium_term" in report
    assert "overall_strength" in report
    
    # Kiểm tra các key cấp hai
    assert "direction" in report['long_term']
    assert "status" in report['long_term']
    assert "direction" in report['medium_term']
    assert "status" in report['medium_term']
    assert "adx_direction" in report['medium_term']

    # Kiểm tra giá trị
    assert report['long_term']['direction'] == "Uptrend"
    assert report['medium_term']['direction'] == "Uptrend"
    assert report['overall_strength']['strength'] == "Strong"

def test_handling_missing_columns():
    """Kiểm tra xem analyzer có xử lý được khi thiếu cột dữ liệu không."""
    # Thiếu cột SMA_200
    df = pd.DataFrame([{'SMA_50': 140}], index=[pd.to_datetime("2025-01-01")])
    analyzer = DailyTrendAnalyzer(df)
    report = analyzer._get_long_term_view()
    
    assert report['direction'] == "Undefined"