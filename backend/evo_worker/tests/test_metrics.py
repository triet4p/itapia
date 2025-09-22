from datetime import datetime, timezone

import numpy as np
import pytest
from app.backtest.trade import Trade
from app.performances.metrics import PerformanceMetricsCalculator


def create_mock_trades():
    """Create a set of mock trades for testing."""
    trades = [
        # Trade 1: Winning long trade
        Trade(
            ticker="AAPL",
            action_type="LONG",
            entry_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            entry_price=100.0,
            exit_date=datetime(2023, 1, 5, tzinfo=timezone.utc),
            exit_price=110.0,  # 10% gain
            exit_reason="TAKE_PROFIT",
            position_size_pct=1.0,
        ),
        # Trade 2: Losing long trade
        Trade(
            ticker="GOOGL",
            action_type="LONG",
            entry_date=datetime(2023, 1, 10, tzinfo=timezone.utc),
            entry_price=2000.0,
            exit_date=datetime(2023, 1, 15, tzinfo=timezone.utc),
            exit_price=1900.0,  # 5% loss
            exit_reason="STOP_LOSS",
            position_size_pct=1.0,
        ),
        # Trade 3: Winning short trade
        Trade(
            ticker="TSLA",
            action_type="SHORT",
            entry_date=datetime(2023, 2, 1, tzinfo=timezone.utc),
            entry_price=200.0,
            exit_date=datetime(2023, 2, 10, tzinfo=timezone.utc),
            exit_price=180.0,  # 10% gain (short)
            exit_reason="TAKE_PROFIT",
            position_size_pct=1.0,
        ),
        # Trade 4: Losing short trade
        Trade(
            ticker="MSFT",
            action_type="SHORT",
            entry_date=datetime(2023, 2, 15, tzinfo=timezone.utc),
            entry_price=300.0,
            exit_date=datetime(2023, 2, 20, tzinfo=timezone.utc),
            exit_price=330.0,  # 10% loss (short)
            exit_reason="STOP_LOSS",
            position_size_pct=1.0,
        ),
    ]
    return trades


def test_performance_metrics_initialization():
    """Test that PerformanceMetrics initializes correctly."""
    # Test with empty trade log
    metrics_empty = PerformanceMetricsCalculator([])
    assert metrics_empty.trade_log == []
    assert metrics_empty.trades_df.empty
    assert metrics_empty.initial_capital == 100000.0

    # Test with trades
    trades = create_mock_trades()
    metrics = PerformanceMetricsCalculator(trades)
    assert len(metrics.trade_log) == 4
    assert len(metrics.trades_df) == 4
    assert metrics.initial_capital == 100000.0


def test_create_trades_dataframe():
    """Test the _create_trades_dataframe method."""
    trades = create_mock_trades()
    metrics = PerformanceMetricsCalculator(trades)

    df = metrics._create_trades_dataframe()
    assert len(df) == 4
    assert "profit_pct" in df.columns
    assert "duration_days" in df.columns
    assert "exit_date" in df.columns
    assert df.index.name == "exit_date"

    # Check profit calculations
    assert df.iloc[0]["profit_pct"] == 0.1  # 10% gain
    assert df.iloc[1]["profit_pct"] == -0.05  # 5% loss
    assert df.iloc[2]["profit_pct"] == 0.1  # 10% gain (short)
    assert df.iloc[3]["profit_pct"] == -0.1  # 10% loss (short)


def test_calculate_equity_curve():
    """Test the calculate_equity_curve method."""
    trades = create_mock_trades()
    metrics = PerformanceMetricsCalculator(trades)

    equity_curve = metrics.calculate_equity_curve()
    assert len(equity_curve) == 5  # Initial capital + 4 trades
    assert equity_curve.iloc[0] == 100000.0  # Initial capital


def test_calculate_total_return():
    """Test the calculate_total_return method."""
    trades = create_mock_trades()
    metrics = PerformanceMetricsCalculator(trades)

    total_return = metrics.calculate_total_return()
    # The calculation uses compounding returns:
    # Initial capital: 100000
    # Trade 1: 10% gain on 100% position = 1.10 factor -> 110000
    # Trade 2: 5% loss on 100% position = 0.95 factor -> 110000 * 0.95 = 104500
    # Trade 3: 10% gain on 100% position = 1.10 factor -> 104500 * 1.10 = 114950
    # Trade 4: 10% loss on 100% position = 0.90 factor -> 114950 * 0.90 = 103455
    # Total return: (103455 - 100000) / 100000 = 0.03455
    expected_return = 0.03455
    # Using pytest.approx for floating point comparison
    assert total_return == pytest.approx(expected_return, abs=1e-10)


def test_calculate_max_drawdown():
    """Test the calculate_max_drawdown method."""
    # Create trades that result in a clear drawdown
    trades = [
        # Trade 1: Big loss
        Trade(
            ticker="TEST",
            action_type="LONG",
            entry_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            entry_price=100.0,
            exit_date=datetime(2023, 1, 5, tzinfo=timezone.utc),
            exit_price=50.0,  # 50% loss
            exit_reason="STOP_LOSS",
            position_size_pct=1.0,
        ),
        # Trade 2: Recovery
        Trade(
            ticker="TEST2",
            action_type="LONG",
            entry_date=datetime(2023, 1, 10, tzinfo=timezone.utc),
            entry_price=100.0,
            exit_date=datetime(2023, 1, 15, tzinfo=timezone.utc),
            exit_price=150.0,  # 50% gain
            exit_reason="TAKE_PROFIT",
            position_size_pct=1.0,
        ),
    ]
    metrics = PerformanceMetricsCalculator(trades)
    max_dd = metrics.calculate_max_drawdown()
    # With a 50% loss followed by a 50% gain, max drawdown should be 50%
    assert abs(max_dd - 0.5) < 0.01


def test_calculate_win_rate():
    """Test the calculate_win_rate method."""
    trades = create_mock_trades()
    metrics = PerformanceMetricsCalculator(trades)

    win_rate = metrics.calculate_win_rate()
    # 2 winning trades out of 4 total trades = 50%
    assert win_rate == 0.5


def test_calculate_profit_factor():
    """Test the calculate_profit_factor method."""
    trades = create_mock_trades()
    metrics = PerformanceMetricsCalculator(trades)

    profit_factor = metrics.calculate_profit_factor()
    # Gross profit: 10% + 10% = 20%
    # Gross loss: 5% + 10% = 15%
    # Profit factor = 20/15 = 1.3333...
    expected_pf = 20.0 / 15.0
    assert abs(profit_factor - expected_pf) < 0.0001


def test_calculate_sharpe_ratio():
    """Test the calculate_sharpe_ratio method."""
    trades = create_mock_trades()
    metrics = PerformanceMetricsCalculator(trades)

    sharpe = metrics.calculate_sharpe_ratio()
    # Should be a valid number (not NaN or infinity)
    assert isinstance(sharpe, float)
    assert not np.isnan(sharpe)
    assert not np.isinf(sharpe)


def test_calculate_sortino_ratio():
    """Test the calculate_sortino_ratio method."""
    trades = create_mock_trades()
    metrics = PerformanceMetricsCalculator(trades)

    sortino = metrics.calculate_sortino_ratio()
    # Should be a valid number (not NaN or infinity)
    assert isinstance(sortino, float)
    assert not np.isnan(sortino)
    assert not np.isinf(sortino)


def test_calculate_annual_return_stability():
    """Test the calculate_annual_return_stability method."""
    trades = create_mock_trades()
    metrics = PerformanceMetricsCalculator(trades)

    stability = metrics.calculate_annual_return_stability()
    # Should be a valid number
    assert isinstance(stability, float)
    assert not np.isnan(stability)
    assert not np.isinf(stability)


def test_summary():
    """Test the summary method."""
    trades = create_mock_trades()
    metrics = PerformanceMetricsCalculator(trades)

    summary = metrics.summary()

    # Check that all expected fields are present
    assert summary.num_trades == 4
    assert isinstance(summary.total_return_pct, float)
    assert isinstance(summary.max_drawdown_pct, float)
    assert isinstance(summary.win_rate_pct, float)
    assert isinstance(summary.profit_factor, float)
    assert isinstance(summary.sharpe_ratio, float)
    assert isinstance(summary.sortino_ratio, float)
    assert isinstance(summary.annual_return_stability, float)


def test_empty_trades():
    """Test all methods with empty trade log."""
    metrics = PerformanceMetricsCalculator([])

    # All methods should return appropriate default values for empty trade log
    assert metrics.calculate_total_return() == 0.0
    assert metrics.calculate_max_drawdown() == 0.0
    assert metrics.calculate_win_rate() == 0.0
    assert metrics.calculate_profit_factor() == 0.0
    assert metrics.calculate_sharpe_ratio() == 0.0
    assert metrics.calculate_sortino_ratio() == 0.0
    assert metrics.calculate_annual_return_stability() == 999  # Special case

    summary = metrics.summary()
    assert summary.num_trades == 0
    assert summary.total_return_pct == 0.0
    assert summary.max_drawdown_pct == 0.0
    assert summary.win_rate_pct == 0.0
    assert summary.profit_factor == 0.0
    assert summary.sharpe_ratio == 0.0
    assert summary.sortino_ratio == 0.0
    assert summary.annual_return_stability == 0.0  # Overridden in summary


def test_single_trade():
    """Test with a single trade."""
    trades = [
        Trade(
            ticker="TEST",
            action_type="LONG",
            entry_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            entry_price=100.0,
            exit_date=datetime(2023, 1, 5, tzinfo=timezone.utc),
            exit_price=110.0,  # 10% gain
            exit_reason="TAKE_PROFIT",
            position_size_pct=1.0,
        )
    ]
    metrics = PerformanceMetricsCalculator(trades)

    # Test that methods handle single trade correctly
    assert metrics.calculate_total_return() == pytest.approx(0.1, abs=1e-10)  # 10% gain
    assert metrics.calculate_win_rate() == 1.0  # 100% win rate
    # Profit factor should be high since there are only profits
    assert metrics.calculate_profit_factor() == 9999.0  # Special case for no losses
    # Sharpe ratio should return 0.0 for insufficient data
    assert metrics.calculate_sharpe_ratio() == 0.0


def test_profit_factor_edge_cases():
    """Test profit factor calculation edge cases."""
    # Test case: No winning trades
    losing_trades = [
        Trade(
            ticker="TEST",
            action_type="LONG",
            entry_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            entry_price=100.0,
            exit_date=datetime(2023, 1, 5, tzinfo=timezone.utc),
            exit_price=90.0,  # 10% loss
            exit_reason="STOP_LOSS",
            position_size_pct=1.0,
        )
    ]
    metrics = PerformanceMetricsCalculator(losing_trades)
    profit_factor = metrics.calculate_profit_factor()
    # No profits, only losses -> profit factor = 0
    assert profit_factor == 0.0

    # Test case: All trades break even
    breakeven_trades = [
        Trade(
            ticker="TEST",
            action_type="LONG",
            entry_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            entry_price=100.0,
            exit_date=datetime(2023, 1, 5, tzinfo=timezone.utc),
            exit_price=100.0,  # 0% gain/loss
            exit_reason="TIME_STOP",
            position_size_pct=1.0,
        )
    ]
    metrics = PerformanceMetricsCalculator(breakeven_trades)
    profit_factor = metrics.calculate_profit_factor()
    # No profits, no losses -> profit factor = 1 (break even)
    assert profit_factor == 1.0


def test_only_winning_trades():
    """Test with only winning trades."""
    winning_trades = [
        Trade(
            ticker="WIN1",
            action_type="LONG",
            entry_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            entry_price=100.0,
            exit_date=datetime(2023, 1, 5, tzinfo=timezone.utc),
            exit_price=110.0,  # 10% gain
            exit_reason="TAKE_PROFIT",
            position_size_pct=1.0,
        ),
        Trade(
            ticker="WIN2",
            action_type="SHORT",
            entry_date=datetime(2023, 1, 10, tzinfo=timezone.utc),
            entry_price=200.0,
            exit_date=datetime(2023, 1, 15, tzinfo=timezone.utc),
            exit_price=180.0,  # 10% gain (short)
            exit_reason="TAKE_PROFIT",
            position_size_pct=1.0,
        ),
    ]
    metrics = PerformanceMetricsCalculator(winning_trades)

    # Win rate should be 100%
    assert metrics.calculate_win_rate() == 1.0

    # Profit factor should be high
    profit_factor = metrics.calculate_profit_factor()
    assert profit_factor == 9999.0  # Special case for no losses

    # Total return should be positive
    total_return = metrics.calculate_total_return()
    # Trade 1: 10% gain -> 1.10 factor
    # Trade 2: 10% gain -> 1.10 factor
    # Combined: 1.10 * 1.10 = 1.21 -> 21% total gain
    assert total_return == pytest.approx(0.21, abs=1e-10)


def test_sortino_ratio_edge_cases():
    """Test Sortino ratio calculation edge cases."""
    # Test with only positive returns (no downside risk)
    winning_trades = [
        Trade(
            ticker="WIN1",
            action_type="LONG",
            entry_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            entry_price=100.0,
            exit_date=datetime(2023, 1, 5, tzinfo=timezone.utc),
            exit_price=110.0,  # 10% gain
            exit_reason="TAKE_PROFIT",
            position_size_pct=1.0,
        ),
        Trade(
            ticker="WIN2",
            action_type="LONG",
            entry_date=datetime(2023, 1, 10, tzinfo=timezone.utc),
            entry_price=200.0,
            exit_date=datetime(2023, 1, 15, tzinfo=timezone.utc),
            exit_price=220.0,  # 10% gain
            exit_reason="TAKE_PROFIT",
            position_size_pct=1.0,
        ),
    ]
    metrics = PerformanceMetricsCalculator(winning_trades)
    sortino = metrics.calculate_sortino_ratio()
    # With only positive returns, downside deviation should be 0,
    # which would normally cause a division by zero, but the function handles this
    assert isinstance(sortino, float)
    assert not np.isnan(sortino)
    assert not np.isinf(sortino)


def test_stability_short_duration():
    """Test annual_return_stability with short duration trades (less than 1 year)."""
    # Create trades that occur within a 6-month period
    short_trades = [
        Trade(
            ticker="SHORT1",
            action_type="LONG",
            entry_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            entry_price=100.0,
            exit_date=datetime(2023, 1, 5, tzinfo=timezone.utc),
            exit_price=110.0,  # 10% gain
            exit_reason="TAKE_PROFIT",
            position_size_pct=1.0,
        ),
        Trade(
            ticker="SHORT2",
            action_type="LONG",
            entry_date=datetime(2023, 3, 1, tzinfo=timezone.utc),
            entry_price=200.0,
            exit_date=datetime(2023, 3, 10, tzinfo=timezone.utc),
            exit_price=180.0,  # 10% loss
            exit_reason="STOP_LOSS",
            position_size_pct=1.0,
        ),
    ]
    metrics = PerformanceMetricsCalculator(short_trades)
    stability = metrics.calculate_annual_return_stability()
    # Since the trades occur within less than a year, should return penalty value of 1.0
    assert stability == pytest.approx(1.0, abs=1e-10)


def test_stability_multiple_years_known_std():
    """Test annual_return_stability with known returns over multiple years."""
    # Create trades that span multiple years with known annual returns
    multi_year_trades = [
        # Year 2022 trades
        Trade(
            ticker="Y2022_1",
            action_type="LONG",
            entry_date=datetime(2022, 3, 1, tzinfo=timezone.utc),
            entry_price=100.0,
            exit_date=datetime(2022, 3, 5, tzinfo=timezone.utc),
            exit_price=105.0,  # 5% gain
            exit_reason="TAKE_PROFIT",
            position_size_pct=1.0,
        ),
        Trade(
            ticker="Y2022_2",
            action_type="LONG",
            entry_date=datetime(2022, 8, 1, tzinfo=timezone.utc),
            entry_price=200.0,
            exit_date=datetime(2022, 8, 10, tzinfo=timezone.utc),
            exit_price=210.0,  # 5% gain
            exit_reason="TAKE_PROFIT",
            position_size_pct=1.0,
        ),
        # Year 2023 trades
        Trade(
            ticker="Y2023_1",
            action_type="LONG",
            entry_date=datetime(2023, 2, 1, tzinfo=timezone.utc),
            entry_price=100.0,
            exit_date=datetime(2023, 2, 5, tzinfo=timezone.utc),
            exit_price=120.0,  # 20% gain
            exit_reason="TAKE_PROFIT",
            position_size_pct=1.0,
        ),
        Trade(
            ticker="Y2023_2",
            action_type="LONG",
            entry_date=datetime(2023, 9, 1, tzinfo=timezone.utc),
            entry_price=300.0,
            exit_date=datetime(2023, 9, 10, tzinfo=timezone.utc),
            exit_price=270.0,  # 10% loss
            exit_reason="STOP_LOSS",
            position_size_pct=1.0,
        ),
    ]
    metrics = PerformanceMetricsCalculator(multi_year_trades)
    stability = metrics.calculate_annual_return_stability()

    # Calculate expected standard deviation manually:
    # Year 2022 total return: 5% + 5% = 10% or 0.10
    # Year 2023 total return: 20% - 10% = 10% or 0.10
    # Standard deviation of [0.10, 0.10] = 0.0
    expected_stability = 0.0
    assert stability == pytest.approx(expected_stability, abs=1e-10)
