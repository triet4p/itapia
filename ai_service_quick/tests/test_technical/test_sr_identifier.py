# ai_service/tests/test_technical/test_support_resistance_identifier.py

import pytest
import pandas as pd
import numpy as np

# Import lớp cần test
from app.technical.analysis_engine.sr_identifier import SupportResistanceIdentifier

# --- Dữ liệu giả lập (Fixture) ---
@pytest.fixture(scope="module")
def sample_enriched_data() -> pd.DataFrame:
    """
    Tạo ra một DataFrame đã được làm giàu, mô phỏng output của FeatureEngine.
    """
    # Tạo 100 dòng dữ liệu
    dates = pd.date_range(start="2023-01-01", periods=100)
    data = {
        'open': np.linspace(100, 150, 100),
        'high': np.linspace(102, 155, 100),
        'low': np.linspace(98, 148, 100),
        'close': np.linspace(101, 152, 100),
        'volume': np.linspace(1e6, 2e6, 100),
        # Thêm các cột chỉ báo giả lập
        'SMA_20': np.linspace(90, 145, 100),
        'SMA_50': np.linspace(80, 135, 100),
        'SMA_200': np.linspace(70, 125, 100), # Sẽ không đủ dữ liệu 200 nên sẽ có NaN
        'BBU_20_2.0': np.linspace(95, 150, 100),
        'BBL_20_2.0': np.linspace(85, 140, 100),
        'BBM_20_2.0': np.linspace(90, 145, 100),
    }
    df = pd.DataFrame(data, index=dates)
    # Giả lập NaN cho các chỉ báo dài hạn
    df.loc[df.index[:60], 'SMA_200'] = np.nan
    return df

# --- Các bài test cho SupportResistanceIdentifier ---

def test_sr_identifier_initialization(sample_enriched_data):
    """Kiểm tra khởi tạo thành công và xử lý lỗi."""
    # Test khởi tạo thành công
    identifier = SupportResistanceIdentifier(sample_enriched_data, history_window=90)
    assert identifier.current_price == sample_enriched_data['close'].iloc[-1]
    assert len(identifier.analysis_df) == 90

    # Test lỗi khi không đủ dữ liệu
    with pytest.raises(ValueError, match="at least 90 rows"):
        SupportResistanceIdentifier(sample_enriched_data.head(50), history_window=90)

def test_get_dynamic_levels(sample_enriched_data):
    """Kiểm tra việc lấy các mức S/R động từ MA và BB."""
    identifier = SupportResistanceIdentifier(sample_enriched_data)
    levels = identifier._get_dynamic_levels_from_ma_bb()
    
    latest_row = sample_enriched_data.iloc[-1]
    
    assert isinstance(levels, list)
    # Kiểm tra xem các giá trị có đúng không
    assert (latest_row['SMA_50'], 'SMA_50') in levels
    assert (latest_row['BBU_20_2.0'], 'BBU_20_2.0') in levels
    assert (latest_row['BBL_20_2.0'], 'BBL_20_2.0') in levels
    # Kiểm tra không lấy giá trị NaN
    assert not any(pd.isna(level) for level in levels)

def test_get_pivot_point_levels(sample_enriched_data):
    """Kiểm tra tính toán Pivot Points."""
    identifier = SupportResistanceIdentifier(sample_enriched_data)
    levels = identifier._get_pivot_point_levels()

    assert isinstance(levels, list)
    assert len(levels) == 7 # PP, R1-3, S1-3

    # Kiểm tra tính toán thủ công với giá trị cuối
    prev_row = sample_enriched_data.iloc[-2]
    H, L, C = prev_row['high'], prev_row['low'], prev_row['close']
    expected_pp = (H + L + C) / 3
    
    assert np.isclose(levels[0][0], expected_pp)

def test_get_simple_fibonacci_levels(sample_enriched_data):
    """Kiểm tra tính toán Fibonacci đơn giản."""
    identifier = SupportResistanceIdentifier(sample_enriched_data, history_window=90)
    levels = identifier._get_simple_fibonacci_levels()
    
    analysis_df = sample_enriched_data.tail(90)
    swing_high = analysis_df['high'].max()
    swing_low = analysis_df['low'].min()
    price_range = swing_high - swing_low
    
    assert isinstance(levels, list)
    assert len(levels) == 10 # 5 tỷ lệ mặc định
    
    # Kiểm tra mức Fib 0.5
    expected_fib_50 = swing_high - price_range * 0.5
    assert np.isclose(levels[4][0], expected_fib_50)

def test_placeholder_v2_functions_return_empty():
    """Đảm bảo các hàm placeholder cho v2 trả về danh sách rỗng."""
    # --- THAY ĐỔI CHÍNH Ở ĐÂY ---
    # Tạo DataFrame nhỏ với DatetimeIndex
    dates = pd.date_range(start="2023-01-01", periods=5)
    df = pd.DataFrame({
        'close': [1,2,3,4,5], 'high': [1,2,3,4,5], 'low': [1,2,3,4,5], 
        'open': [1,2,3,4,5], 'volume': [1,2,3,4,5]
    }, index=dates)
    
    identifier = SupportResistanceIdentifier(df, history_window=3)
    
    assert identifier._get_levels_from_extrema_v2() == []
    assert identifier._get_advanced_fibonacci_levels_v2() == []

def test_identify_levels_full_logic(sample_enriched_data):
    """Kiểm tra hàm tổng hợp cuối cùng."""
    identifier = SupportResistanceIdentifier(sample_enriched_data)
    report = identifier.identify_levels()
    
    assert "support" in report
    assert "resistance" in report
    
    # Kiểm tra kiểu dữ liệu
    assert isinstance(report["support"], list)
    assert isinstance(report["resistance"], list)
    
    current_price = sample_enriched_data.iloc[-1]['close']
    
    # Tất cả các mức support phải nhỏ hơn giá hiện tại
    if report["support"]:
        assert all(s['level'] < current_price for s in report["support"])
        # Kiểm tra sắp xếp giảm dần
        assert report["support"] == sorted(report['support'], key=lambda x: x['level'], reverse=True)
        
    # Tất cả các mức resistance phải lớn hơn hoặc bằng giá hiện tại
    if report["resistance"]:
        assert all(r['level'] >= current_price for r in report["resistance"])
        # Kiểm tra sắp xếp tăng dần
        assert report["resistance"] == sorted(report['resistance'], key=lambda x: x['level'])