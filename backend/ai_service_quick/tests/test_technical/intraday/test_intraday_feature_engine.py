import numpy as np
import pandas as pd
import pytest
from app.analysis.technical.feature_engine import IntradayFeatureEngine


@pytest.fixture(scope="module")
def sample_intraday_data() -> pd.DataFrame:
    """
    Tạo ra một DataFrame OHLCV intraday (15 phút) mẫu cho 2 ngày giao dịch.
    """
    # Ngày 1
    dates1 = pd.to_datetime(
        pd.date_range(start="2024-05-20 09:30", end="2024-05-20 16:00", freq="15min")
    )
    # Ngày 2
    dates2 = pd.to_datetime(
        pd.date_range(start="2024-05-21 09:30", end="2024-05-21 16:00", freq="15min")
    )

    all_dates = dates1.union(dates2)
    size = len(all_dates)

    data = {
        "open": np.random.uniform(150, 152, size=size),
        "high": np.random.uniform(152, 154, size=size),
        "low": np.random.uniform(148, 150, size=size),
        "close": np.random.uniform(150, 153, size=size),
        "volume": np.random.randint(10000, 50000, size=size),
    }
    df = pd.DataFrame(data, index=all_dates)
    return df


# --- Các bài test cho IntradayFeatureEngine ---


def test_intraday_engine_requires_datetimeindex(sample_intraday_data):
    """Kiểm tra xem engine có ném lỗi không nếu index không phải DatetimeIndex."""
    # Tạo dữ liệu với RangeIndex
    df_no_datetime = sample_intraday_data.reset_index(drop=True)

    with pytest.raises(TypeError, match="index must be a DatetimeIndex"):
        IntradayFeatureEngine(df_no_datetime)


def test_default_intraday_indicators(sample_intraday_data):
    """Kiểm tra xem các chỉ báo mặc định có đúng cho intraday không."""
    engine = IntradayFeatureEngine(sample_intraday_data)
    engine.add_all_intraday_features()

    df = engine.get_features(handle_na_method=None)

    # Kiểm tra sự tồn tại của các cột theo DEFAULT_CONFIG
    assert "EMA_9" in df.columns
    assert "EMA_26" in df.columns
    assert "MACD_12_26_9" in df.columns
    assert "RSI_14" in df.columns
    assert "BBU_26_2.0" in df.columns
    assert "VWAP_D" in df.columns  # pandas-ta thường đặt tên VWAP là VWAP_D
    assert "OR_30m_High" in df.columns


def test_add_opening_range(sample_intraday_data):
    """
    Kiểm tra logic của hàm add_opening_range một cách chi tiết.
    """
    engine = IntradayFeatureEngine(sample_intraday_data)
    engine.add_opening_range(minutes=30)

    df = engine.get_features(handle_na_method=None)

    # --- Kiểm tra cho Ngày 1 ---
    date1_str = "2024-05-20"
    df_day1 = df[df.index.date == pd.to_datetime(date1_str).date()]

    # Vùng giá 30 phút đầu tiên (9:30, 9:45)
    or_day1_df = df_day1.iloc[0:2]
    expected_or_high_day1 = or_day1_df["high"].max()
    expected_or_low_day1 = or_day1_df["low"].min()

    # Kiểm tra xem tất cả các giá trị OR trong ngày có giống nhau và đúng không
    assert (df_day1["OR_30m_High"] == expected_or_high_day1).all()
    assert (df_day1["OR_30m_Low"] == expected_or_low_day1).all()

    # --- Kiểm tra cho Ngày 2 ---
    date2_str = "2024-05-21"
    df_day2 = df[df.index.date == pd.to_datetime(date2_str).date()]

    or_day2_df = df_day2.iloc[0:2]
    expected_or_high_day2 = or_day2_df["high"].max()
    expected_or_low_day2 = or_day2_df["low"].min()

    assert (df_day2["OR_30m_High"] == expected_or_high_day2).all()
    assert (df_day2["OR_30m_Low"] == expected_or_low_day2).all()

    # Đảm bảo OR của ngày 1 và ngày 2 là khác nhau
    assert expected_or_high_day1 != expected_or_high_day2


def test_vwap_resets_daily(sample_intraday_data):
    """
    Kiểm tra xem VWAP có được reset mỗi ngày hay không.
    Cách kiểm tra gián tiếp: VWAP của cây nến đầu tiên phải bằng giá trung bình của chính nó.
    """
    engine = IntradayFeatureEngine(sample_intraday_data)
    engine.add_intraday_volume()

    df = engine.get_features(handle_na_method=None)

    # Ngày 1
    first_candle_day1 = df.loc["2024-05-20 09:30:00"]
    expected_vwap_day1 = (
        first_candle_day1["high"]
        + first_candle_day1["low"]
        + first_candle_day1["close"]
    ) / 3
    assert np.isclose(first_candle_day1["VWAP_D"], expected_vwap_day1)

    # Ngày 2
    first_candle_day2 = df.loc["2024-05-21 09:30:00"]
    expected_vwap_day2 = (
        first_candle_day2["high"]
        + first_candle_day2["low"]
        + first_candle_day2["close"]
    ) / 3
    assert np.isclose(first_candle_day2["VWAP_D"], expected_vwap_day2)

    # VWAP của cây nến thứ hai phải khác
    second_candle_day1 = df.loc["2024-05-20 09:45:00"]
    assert not np.isclose(second_candle_day1["VWAP_D"], expected_vwap_day1)
