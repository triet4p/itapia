# app/intraday_demo.py
import pandas as pd
import numpy as np
import json

# Import các lớp Intraday cần thiết
from app.technical.feature_engine import IntradayFeatureEngine
from app.technical.analysis_engine.intraday.engine import IntradayAnalysisEngine

def generate_mock_intraday_ohlcv(start_time="2024-05-21 09:30", periods=27, freq="15min") -> pd.DataFrame:
    """
    Tạo dữ liệu OHLCV 15 phút giả lập cho một ngày giao dịch,
    mô phỏng một kịch bản "Opening Range Breakout".
    """
    dates = pd.to_datetime(pd.date_range(start=start_time, periods=periods, freq=freq))
    size = len(dates)
    
    # Tạo một chuỗi giá cơ bản
    base_price = 150.0
    price_seq = []
    
    # Kịch bản: Mở cửa, đi ngang trong 30-45 phút, sau đó bùng nổ tăng giá
    for i in range(size):
        if i < 3: # 45 phút đầu đi ngang
            price_change = np.random.uniform(-0.2, 0.2)
        elif i < 10: # Bắt đầu tăng nhẹ
            price_change = np.random.uniform(0.1, 0.5)
        else: # Tăng mạnh hơn về cuối ngày
            price_change = np.random.uniform(0.2, 0.8)
        
        base_price += price_change
        price_seq.append(base_price)

    df = pd.DataFrame(index=dates)
    df['close'] = price_seq
    df['open'] = df['close'].shift(1).fillna(method='bfill') - np.random.uniform(-0.1, 0.1, size)
    df['high'] = df[['open', 'close']].max(axis=1) + np.random.uniform(0, 0.5, size)
    df['low'] = df[['open', 'close']].min(axis=1) - np.random.uniform(0, 0.5, size)
    # Khối lượng tăng dần về cuối ngày
    df['volume'] = np.linspace(10000, 50000, size).astype(int)
    
    return df

if __name__ == "__main__":
    print("1. Generating mock Intraday OHLCV data...")
    # Tạo dữ liệu cho một ngày giao dịch đầy đủ (26 cây nến 15 phút)
    mock_intraday_df = generate_mock_intraday_ohlcv(periods=26)

    print("\n2. Running IntradayFeatureEngine to enrich data...")
    intraday_feature_engine = IntradayFeatureEngine(mock_intraday_df)
    
    # Chạy quy trình tạo feature intraday
    enriched_intraday_df = (intraday_feature_engine
                           .add_all_intraday_features()
                           .get_features(handle_na_method=None))

    if enriched_intraday_df.empty:
        print("Not enough data after enrichment. Exiting.")
    else:
        print(f"\n3. Enriched Intraday DataFrame created with {len(enriched_intraday_df)} rows.")
        
        print("\n4. Initializing and running IntradayAnalysisEngine...")
        intraday_analysis_engine = IntradayAnalysisEngine(enriched_intraday_df)
        
        # Lấy báo cáo phân tích trong ngày
        intraday_report = intraday_analysis_engine.get_analysis_report()
        
        print("\n\n--- FINAL INTRADAY ANALYSIS REPORT ---")
        # Sử dụng json.dumps để in dict một cách đẹp đẽ
        print(json.dumps(intraday_report, indent=2))