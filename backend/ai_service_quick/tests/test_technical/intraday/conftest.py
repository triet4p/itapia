import numpy as np
import pandas as pd
import pytest


@pytest.fixture(scope="session")
def sample_intraday_data_for_analysis() -> pd.DataFrame:
    """
    Tạo dữ liệu intraday giả lập đã được làm giàu, mô phỏng output
    từ IntradayFeatureEngine.
    """
    dates = pd.to_datetime(
        pd.date_range(start="2024-05-21 09:30", periods=27, freq="15min")
    )
    size = len(dates)

    data = {
        "open": np.linspace(150, 155, size),
        "high": np.linspace(151, 156, size),
        "low": np.linspace(149, 154, size),
        "close": np.linspace(150.5, 155.5, size),
        "volume": np.random.randint(10000, 50000, size=size),
        "VWAP_D": np.linspace(150.2, 155.2, size),
        "RSI_14": np.full(size, 80),  # Giả lập trạng thái Overbought
        "MACD_12_26_9": np.full(size, 1.5),
        "MACDs_12_26_9": np.full(size, 1.2),  # Giả lập Bullish Crossover
        "OR_30m_High": np.full(size, 151.5),
        "OR_30m_Low": np.full(size, 150.0),
    }
    df = pd.DataFrame(data, index=dates)
    # Giả lập giá cuối cùng phá vỡ lên trên Opening Range
    df.iloc[-1, df.columns.get_loc("close")] = 156.0
    return df
