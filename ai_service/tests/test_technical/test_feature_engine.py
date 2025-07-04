import pytest
import pandas as pd
import numpy as np

# Import lớp cần test
from app.technical.feature_engine import FeatureEngine

# --- Dữ liệu giả lập (Fixture) để tái sử dụng ---
@pytest.fixture(scope="module")
def sample_ohlcv_data() -> pd.DataFrame:
    """
    Tạo ra một DataFrame OHLCV mẫu để sử dụng trong các test.
    Sử dụng scope="module" để dữ liệu này chỉ được tạo một lần cho tất cả các test trong file.
    """
    data = {
        'open': np.random.uniform(95, 105, size=100),
        'high': np.random.uniform(100, 110, size=100),
        'low': np.random.uniform(90, 100, size=100),
        'close': np.random.uniform(98, 108, size=100),
        'volume': np.random.uniform(1e6, 5e6, size=100)
    }
    df = pd.DataFrame(data)
    # Đảm bảo cột high luôn cao nhất và low luôn thấp nhất
    df['high'] = df[['open', 'close']].max(axis=1) + np.random.uniform(0, 5, size=100)
    df['low'] = df[['open', 'close']].min(axis=1) - np.random.uniform(0, 5, size=100)
    return df

# --- Các bài test cho FeatureEngine ---

def test_feature_engine_initialization(sample_ohlcv_data):
    """Kiểm tra việc khởi tạo có thành công không."""
    engine = FeatureEngine(sample_ohlcv_data)
    assert isinstance(engine.df, pd.DataFrame)
    assert not engine.df.empty
    # Kiểm tra xem có tạo bản sao không (không làm thay đổi df gốc)
    assert id(engine.df) != id(sample_ohlcv_data)

def test_add_sma(sample_ohlcv_data):
    """Kiểm tra hàm add_sma có thêm đúng cột không."""
    engine = FeatureEngine(sample_ohlcv_data)
    engine.add_sma(configs=[{'length': 20}, {'length': 50}])
    
    df = engine.get_features(copy=False, dropna=False) # Lấy df nội bộ
    assert 'SMA_20' in df.columns
    assert 'SMA_50' in df.columns
    # Kiểm tra giá trị đầu tiên của SMA_20 phải là NaN (vì không đủ dữ liệu)
    assert pd.isna(df['SMA_20'].iloc[18])
    # Kiểm tra giá trị cuối cùng phải là một số
    assert pd.notna(df['SMA_20'].iloc[-1])

def test_add_adx_and_dmp_dmn(sample_ohlcv_data):
    """Kiểm tra hàm add_adx có thêm cả 3 cột ADX, DMP, DMN không."""
    engine = FeatureEngine(sample_ohlcv_data)
    engine.add_adx(configs=[{'length': 14}])

    df = engine.get_features(copy=False, dropna=False)
    assert 'ADX_14' in df.columns
    assert 'DMP_14' in df.columns
    assert 'DMN_14' in df.columns

def test_add_trend_indicators_group(sample_ohlcv_data):
    """Kiểm tra hàm nhóm add_trend_indicators."""
    engine = FeatureEngine(sample_ohlcv_data)
    engine.add_trend_indicators() # Sử dụng config mặc định
    
    df = engine.get_features(copy=False, dropna=False)
    # Chỉ kiểm tra một vài cột đại diện
    assert 'SMA_20' in df.columns
    assert 'EMA_50' in df.columns
    assert 'MACD_12_26_9' in df.columns
    assert 'ADX_14' in df.columns

def test_error_handling_for_invalid_param(sample_ohlcv_data, capsys):
    """
    Kiểm tra xem hệ thống có xử lý lỗi một cách duyên dáng khi gặp tham số sai không.
    capsys là một fixture của pytest để bắt output từ print().
    """
    engine = FeatureEngine(sample_ohlcv_data)
    # 'lengt' là tham số sai
    engine.add_sma(configs=[{'lengt': 20}])
    
    captured = capsys.readouterr()
    # Kiểm tra xem có in ra cảnh báo lỗi không
    # Kiểm tra những phần cốt lõi của thông báo
    assert "Warning: Invalid parameter" in captured.out
    assert "'sma'" in captured.out
    assert "'lengt'" in captured.out
    
    df = engine.get_features()
    # Đảm bảo không có cột nào được tạo ra từ config lỗi
    assert 'SMA_20' not in df.columns
    
def test_get_features_dropna_and_reset_index(sample_ohlcv_data):
    """Kiểm tra các tham số của hàm get_features."""
    engine = FeatureEngine(sample_ohlcv_data)
    engine.add_sma(configs=[{'length': 50}]) # Sẽ tạo nhiều NaN ở đầu
    
    # Test dropna=True (mặc định)
    df_dropped = engine.get_features()
    assert df_dropped.isna().sum().sum() == 0
    assert df_dropped.index.is_monotonic_increasing
    
    # Test dropna=False
    df_not_dropped = engine.get_features(dropna=False)
    assert df_not_dropped.isna().sum().sum() > 0