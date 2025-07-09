import pandas as pd
import numpy as np
from typing import List, Dict

# Import lớp cần test
from app.technical.analysis_engine.daily.pattern_recognizer import DailyPatternRecognizer

# --- Hàm Helper để tạo dữ liệu có mẫu hình ---
def create_pattern_df(price_sequence: List[int], cdl_data: Dict[str, int] = None) -> pd.DataFrame:
    """
    Tạo một DataFrame từ một chuỗi giá để kiểm tra các mẫu hình.
    """
    size = len(price_sequence)
    # --- THAY ĐỔI CHÍNH Ở ĐÂY ---
    # Tạo một dải ngày tháng làm index
    dates = pd.date_range(start="2023-01-01", periods=size, freq="D")
    
    df = pd.DataFrame(index=dates) # Sử dụng index mới
    df = pd.DataFrame({
        'open': np.array(price_sequence) - 0.5,
        'high': np.array(price_sequence) + 1.0,
        'low': np.array(price_sequence) - 1.0,
        'close': np.array(price_sequence),
        'volume': np.full(size, 100000)
    })
    
    # Thêm dữ liệu mẫu hình nến nếu có
    if cdl_data:
        for cdl_name, value in cdl_data.items():
            # Thêm cột với giá trị 0 ở mọi nơi, trừ dòng cuối cùng
            cdl_col = np.zeros(size)
            cdl_col[-1] = value
            df[cdl_name] = cdl_col
            
    # Đảm bảo low <= close <= high
    df['low'] = df[['low', 'close', 'open']].min(axis=1)
    df['high'] = df[['high', 'close', 'open']].max(axis=1)
    
    return df

# --- Các bài test cho PatternRecognizer ---

def test_find_candlestick_patterns():
    """Kiểm tra việc nhận dạng mẫu hình nến từ các cột cdl_*."""
    # Dữ liệu có mẫu hình Bullish Engulfing ở dòng cuối
    price_seq = [100, 99, 98]
    cdl_data = {'cdl_engulfing': 100} # Giá trị dương là Bullish
    df = create_pattern_df(price_seq, cdl_data)
    
    recognizer = DailyPatternRecognizer(df, history_window=3)
    patterns = recognizer._find_candlestick_patterns()
    
    pattern_names = [p['sentiment'] + ' ' + p['pattern_name'] for p in patterns]
    
    assert "Bullish Engulfing" in pattern_names

def test_is_double_top_confirmed():
    """Kiểm tra trường hợp có mẫu hình Double Top và đã được xác nhận."""
    # P1=110, P2=110, Neckline=100, Current Price=98 (phá vỡ)
    price_seq = [90, 105, 110, 100, 108, 110, 98]
    df = create_pattern_df(price_seq)
    
    # Giảm prominence để có thể bắt được đỉnh/đáy trong dữ liệu nhỏ
    recognizer = DailyPatternRecognizer(df, history_window=7, prominence_pct=0.01, distance=1)
    
    assert recognizer._is_double_top() is not None
    
    patterns = recognizer.find_patterns()
    pattern_names = [p['pattern_name'] for p in patterns]
    
    assert "Double Top" in pattern_names

def test_is_double_top_not_confirmed():
    """Kiểm tra trường hợp có hình dạng Double Top nhưng chưa phá vỡ."""
    # P1=110, P2=110, Neckline=100, Current Price=101 (chưa phá vỡ)
    price_seq = [90, 105, 110, 100, 108, 110, 101]
    df = create_pattern_df(price_seq)
    
    recognizer = DailyPatternRecognizer(df, history_window=7, prominence_pct=0.01, distance=1)
    
    assert recognizer._is_double_top() is None

def test_is_double_bottom_confirmed():
    """Kiểm tra trường hợp có mẫu hình Double Bottom và đã được xác nhận."""
    # T1=90, T2=90, Neckline=100, Current Price=102 (phá vỡ)
    price_seq = [110, 95, 90, 100, 92, 90, 102]
    df = create_pattern_df(price_seq)
    
    recognizer = DailyPatternRecognizer(df, history_window=7, prominence_pct=0.01, distance=1)
    
    assert recognizer._is_double_bottom() is not None
    
    patterns = recognizer.find_patterns()
    pattern_names = [p['pattern_name'] for p in patterns]
    
    assert "Double Bottom" in pattern_names

def test_is_head_and_shoulders_confirmed():
    """Kiểm tra trường hợp có mẫu hình Head and Shoulders và đã được xác nhận."""
    # Vai trái=110, Đầu=115, Vai phải=110, Neckline=100, Current Price=98 (phá vỡ)
    price_seq = [105, 110, 100, 115, 101, 110, 98]
    df = create_pattern_df(price_seq)
    
    recognizer = DailyPatternRecognizer(df, history_window=7, prominence_pct=0.01, distance=1)
    
    # Debugging: In ra các đỉnh/đáy được tìm thấy
    # print("\nPeaks:\n", recognizer.peaks)
    # print("Troughs:\n", recognizer.troughs)
    
    assert recognizer._is_head_and_shoulders() is not None
    
    patterns = recognizer.find_patterns()
    pattern_names = [p['pattern_name'] for p in patterns]
    
    assert "Head and Shoulders" in pattern_names

def test_no_patterns_found():
    """Kiểm tra trường hợp không có mẫu hình nào rõ ràng."""
    # Một xu hướng tăng đơn giản
    price_seq = [100, 101, 102, 103, 104, 105, 106, 107]
    df = create_pattern_df(price_seq)
    
    recognizer = DailyPatternRecognizer(df, history_window=8, distance=1)
    patterns = recognizer.find_patterns()
    
    # Trả về danh sách rỗng nếu không có gì
    # Hoặc bạn có thể assert "Unknown" tùy theo thiết kế cuối cùng
    assert patterns == []

def test_find_extrema_correctness():
    """Kiểm tra xem hàm _find_extrema có tìm đúng đỉnh/đáy không."""
    # SỬA LẠI DỮ LIỆU: Thêm một cặp đỉnh/đáy nữa
    # Dữ liệu mới: P1=110, T1=100, P2=115, T2=105
    price_seq = [100, 110, 100, 115, 105, 108] 
    df = create_pattern_df(price_seq)
    
    # Giảm distance để bắt được các điểm gần nhau
    recognizer = DailyPatternRecognizer(df, history_window=len(price_seq), prominence_pct=0.01, distance=1)

    peaks = recognizer.peaks
    troughs = recognizer.troughs
    
    # Bây giờ assert này sẽ đúng
    assert len(peaks) == 2
    assert len(troughs) == 2
    
    # Kiểm tra giá trị của các đỉnh
    assert np.isclose(peaks['price'].iloc[0], 111.0)
    assert np.isclose(peaks['price'].iloc[1], 116.0)
    
    # Kiểm tra giá trị của các đáy
    assert np.isclose(troughs['price'].iloc[0], 99.0)
    assert np.isclose(troughs['price'].iloc[1], 104.0)