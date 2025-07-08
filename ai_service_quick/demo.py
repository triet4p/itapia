# app/demo.py
import pandas as pd
import numpy as np
import json

from app.technical.feature_engine import DailyFeatureEngine
from app.technical.analysis_engine import AnalysisEngine

def generate_mock_ohlcv_with_pattern(days=150) -> pd.DataFrame:
    """
    Tạo dữ liệu giả lập có một mẫu hình Double Bottom ngay gần cuối
    và được xác nhận bởi điểm dữ liệu cuối cùng.
    """
    dates = pd.date_range(start="2023-01-01", periods=days, freq="D")
    
    # "Ghép" mẫu hình vào chuỗi giá, gần cuối
    # Chúng ta cần phải làm cho nó mượt mà hơn một chút
    # Thay vì gán cứng, chúng ta sẽ tạo một đoạn dữ liệu chi tiết hơn
    
    # Tái tạo dữ liệu từ đầu
    price_seq = list(np.linspace(100, 130, 1020)) # Giá tăng đến ngày 120
    # Thêm mẫu hình
    price_seq.extend([130, 125, 135, 140, 145, 150, 146, 136, 130, 125]) # T1=125, Neckline=135, T2=125
    
    # Thêm 24 ngày đi ngang sau đó
    price_seq.extend([134] * (days - len(price_seq) - 1))
    
    # Thêm điểm phá vỡ cuối cùng
    price_seq.append(151) # Phá vỡ lên trên neckline 135
    
    df = pd.DataFrame(index=dates)
    df['close'] = price_seq
    # ... (các phần tạo ohlv còn lại giữ nguyên) ...
    df['open'] = df['close'].shift(1).fillna(method='bfill')
    df['high'] = df[['open', 'close']].max(axis=1) + np.random.uniform(0, 1, days)
    df['low'] = df[['open', 'close']].min(axis=1) - np.random.uniform(0, 1, days)
    df['volume'] = np.random.randint(1_000_000, 5_000_000, size=days)
    
    print(df.head(5))
    
    return df

if __name__ == "__main__":
    print("1. Generating mock OHLCV data with a recent pattern...")
    mock_df = generate_mock_ohlcv_with_pattern(days=1050)

    # --- Phần còn lại của file main giữ nguyên ---
    # ... (code để gọi FeatureEngine và AnalysisEngine) ...
    print("\n2. Running FeatureEngine to enrich data...")
    feature_engine = DailyFeatureEngine(mock_df)
    enriched_df = (feature_engine
                   .add_all_features() # Dùng add_all để có đủ chỉ báo
                   .get_features(handle_na_method='forward_fill'))

    if enriched_df.empty:
        print("Not enough data after enrichment. Exiting.")
    else:
        print(f"\n3. Enriched DataFrame created with {len(enriched_df)} rows.")
        print(enriched_df.columns[:50])
        print("\n4. Initializing and running AnalysisEngine...")
        # Giảm distance để bắt được các đỉnh/đáy gần nhau trong dữ liệu giả lập
        analysis_engine = AnalysisEngine(enriched_df, 
                                         history_window=90, 
                                         distance=3, 
                                         prominence_pct=0.01)
        
        full_report = analysis_engine.get_analysis_report()
        
        print("\n\n--- FINAL ANALYSIS REPORT ---")
        print(json.dumps(full_report, indent=2))