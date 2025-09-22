"""Performance metrics calculator for backtesting trading strategies."""

from typing import List, Optional

import numpy as np
import pandas as pd
from app.backtest.trade import Trade
from itapia_common.schemas.entities.performance import PerformanceMetrics


class PerformanceMetricsCalculator:
    """Analyze a trade log and calculate key performance and risk metrics."""

    def __init__(
        self,
        trade_log: List[Trade],
        initial_capital: float = 100000.0,
        risk_free_rate_annual: float = 0.02,
    ):  # Risk-free rate 2%/year
        """Initialize the performance analyzer.

        Args:
            trade_log (List[Trade]): List of completed trades from Simulator
            initial_capital (float): Initial capital to calculate equity curve
            risk_free_rate_annual (float): Annual risk-free rate for Sharpe Ratio calculation
        """
        if not trade_log:
            # If no trades, initialize with empty state
            self.trade_log = []
            self.trades_df = pd.DataFrame()
        else:
            self.trade_log = trade_log
            # Convert trade log to DataFrame for easier vectorized calculations
            self.trades_df = self._create_trades_dataframe()

        self.initial_capital = initial_capital
        self.risk_free_rate_daily = (1 + risk_free_rate_annual) ** (
            1 / 252
        ) - 1  # 252 trading days/year

        # Properties will be calculated lazily
        self._equity_curve: Optional[pd.Series] = None

    def _create_trades_dataframe(self) -> pd.DataFrame:
        """Convert list of Trade objects to a DataFrame.

        Returns:
            pd.DataFrame: DataFrame representation of trade log
        """
        df = pd.DataFrame(self.trade_log)
        df["profit_pct"] = np.array([trade.profit_pct for trade in self.trade_log])
        df["duration_days"] = np.array(
            [trade.duration_days for trade in self.trade_log]
        )
        # Convert dates to datetime type for sorting
        df["exit_date"] = pd.to_datetime(df["exit_date"])
        df.set_index("exit_date", inplace=True, drop=False)
        df.sort_index(inplace=True)
        return df

    def calculate_equity_curve(self) -> pd.Series:
        """Calculate the equity curve based on trading results.

        The equity curve represents account value changes over time.

        Returns:
            pd.Series: Equity curve showing account value progression
        """
        if self._equity_curve is not None:
            return self._equity_curve

        if self.trades_df.empty:
            self._equity_curve = pd.Series([self.initial_capital])
            return self._equity_curve

        # Calculate profit/loss for each trade based on % capital
        self.trades_df["return_pct"] = (
            self.trades_df["profit_pct"] * self.trades_df["position_size_pct"]
        )

        # (1 + return_pct) is the growth factor
        self.trades_df["growth_factor"] = 1 + self.trades_df["return_pct"]

        # Calculate account value after each trade
        self.trades_df["equity"] = (
            self.initial_capital * self.trades_df["growth_factor"].cumprod()
        )

        # Create complete equity curve
        equity_curve = pd.Series(
            self.initial_capital,
            index=[self.trades_df.index.min() - pd.Timedelta(days=1)],
        )
        equity_curve = pd.concat([equity_curve, self.trades_df["equity"]])

        self._equity_curve = equity_curve
        return self._equity_curve

    def calculate_total_return(self) -> float:
        """Calculate total return (%) of the entire trade sequence.

        Returns:
            float: Total return as a percentage
        """
        if self.trades_df.empty:
            return 0.0

        equity_curve = self.calculate_equity_curve()
        final_equity = equity_curve.iloc[-1]
        return (final_equity - self.initial_capital) / self.initial_capital

    def calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown.

        This is an important risk metric that shows the maximum loss from peak.

        Returns:
            float: Maximum drawdown as a percentage
        """
        if self.trades_df.empty:
            return 0.0

        equity_curve = self.calculate_equity_curve()
        # Calculate running maximum
        running_max = equity_curve.cummax()
        # Calculate % drawdown from peak at each point
        drawdown = (equity_curve - running_max) / running_max
        return abs(drawdown.min())

    def calculate_win_rate(self) -> float:
        """Calculate the percentage of profitable trades.

        Returns:
            float: Win rate as a percentage
        """
        if self.trades_df.empty:
            return 0.0

        winning_trades = self.trades_df[self.trades_df["profit_pct"] > 0]
        return len(winning_trades) / len(self.trades_df)

    # Open file evo-worker/app/backtest/metrics.py and replace this function

    def calculate_profit_factor(self) -> float:
        """Calculate Profit Factor.

        (Total % profit from winning trades) / (Total % loss from losing trades).
        This version works directly on `profit_pct` to avoid complex reindex errors.

        Returns:
            float: Profit factor value
        """
        if self.trades_df.empty:
            return 0.0

        # Get the profit_pct column which has been calculated and validated
        trade_returns = self.trades_df["profit_pct"]

        # Calculate total % profit from all winning trades
        gross_profit = trade_returns[trade_returns > 0].sum()

        # Calculate total % loss from all losing trades
        gross_loss = abs(trade_returns[trade_returns < 0].sum())

        # Handle case with no losing trades
        if gross_loss == 0:
            if gross_profit > 0:
                # If no losses but profits, profit factor is infinite.
                # Return a large positive number to show excellent result.
                return 50.0
            else:
                # No profit, no loss (all trades break even).
                # Profit factor is undefined, return 1.0 (break even).
                return 1.0

        return gross_profit / gross_loss

    def calculate_sharpe_ratio(self) -> float:
        """Calculate Sharpe Ratio.

        Measures risk-adjusted return (volatility).
        Higher values are better.

        Returns:
            float: Annualized Sharpe ratio
        """
        if self.trades_df.empty or len(self.trades_df) < 2:
            return 0.0

        # Calculate daily portfolio return rates
        equity_curve = self.calculate_equity_curve()
        daily_returns = equity_curve.pct_change().dropna()

        if daily_returns.std() == 0:
            return 0.0  # Avoid division by zero error

        # Excess returns over risk-free rate
        excess_returns = daily_returns - self.risk_free_rate_daily

        # (Average return / Standard deviation) * sqrt(252) for annualized Sharpe Ratio
        sharpe_ratio = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)
        return sharpe_ratio

    def calculate_sortino_ratio(self, target_return_pct: float = 0.0) -> float:
        """Calculate Sortino Ratio based on RETURNS FROM INDIVIDUAL TRADES for consistent results.

        Args:
            target_return_pct (float): Target return percentage for each trade. Defaults to 0.

        Returns:
            float: Sortino ratio (not annualized, as it's based on trades).
        """
        if self.trades_df.empty or len(self.trades_df) < 2:
            return 0.0

        trade_returns = self.trades_df["profit_pct"]

        # 1. Calculate average return per trade (Numerator)
        avg_return_per_trade = trade_returns.mean()

        # 2. Calculate Downside Deviation based on losing trades (Denominator)
        returns_below_target = trade_returns[trade_returns < target_return_pct]

        if returns_below_target.empty:
            # If no losing trades
            return 50.0 if avg_return_per_trade > 0 else 0.0

        # Calculate standard deviation of losing trades
        downside_deviation = returns_below_target.std(ddof=0)

        if abs(downside_deviation) <= 1e-4:
            # Rare case (all losing trades have the same loss amount)
            # Or only 1 losing trade
            return 50.0 if avg_return_per_trade > 0 else 0.0

        # 3. Calculate Sortino Ratio
        sortino_ratio = (avg_return_per_trade - target_return_pct) / downside_deviation

        # No need to annualize as it's based on events (each trade), not time.
        return sortino_ratio if np.isfinite(sortino_ratio) else 0.0

    def calculate_annual_return_stability(self) -> float:
        """Measure the stability of returns over years.

        Returns standard deviation of annual returns. Lower is better.

        Returns:
            float: Standard deviation of annual returns (lower is better)
        """
        if self.trades_df.empty:
            return 999

        # Ensure return_pct column exists
        if "return_pct" not in self.trades_df.columns:
            self.trades_df["return_pct"] = (
                self.trades_df["profit_pct"] * self.trades_df["position_size_pct"]
            )

        # Group trades by year and calculate total returns
        # Note: This is simple addition, not compound returns, to evaluate raw performance
        annual_returns = self.trades_df["return_pct"].resample("YE").sum()

        if len(annual_returns) < 2:
            # Instead of returning 0.0 (perfect), check if the actual
            # trade duration spans more than a year.
            if not self.trades_df.empty:
                trade_duration = self.trades_df.index.max() - self.trades_df.index.min()
                if trade_duration.days < 365:
                    # If strategy exists for less than 1 year, it's not stable.
                    # Return a large penalty value. 1.0 is a very high standard deviation.
                    return 1.0

            return 0.02

        return annual_returns.std(ddof=0)

    def calculate_cagr(self) -> float:
        """Calculate Compound Annual Growth Rate (CAGR).

        Returns:
            float: Compound annual growth rate
        """
        if self.trades_df.empty:
            return 0.0

        equity_curve = self.calculate_equity_curve()
        final_equity = equity_curve.iloc[-1]

        start_date = equity_curve.index.min()
        end_date = equity_curve.index.max()
        num_days = (end_date - start_date).days

        # If time is less than 1 year, don't calculate CAGR, return total return
        if num_days < 365:
            return self.calculate_total_return()

        num_years = num_days / 365.25

        cagr = (final_equity / self.initial_capital) ** (1 / num_years) - 1
        return cagr

    def summary(self) -> PerformanceMetrics:
        """Consolidate all performance metrics into a dictionary.

        Returns:
            PerformanceMetrics: Complete performance metrics report
        """
        if self.trades_df.empty:
            return PerformanceMetrics()

        return PerformanceMetrics(
            num_trades=len(self.trade_log),
            total_return_pct=self.calculate_total_return(),
            max_drawdown_pct=self.calculate_max_drawdown(),
            win_rate_pct=self.calculate_win_rate(),
            profit_factor=self.calculate_profit_factor(),
            sharpe_ratio=self.calculate_sharpe_ratio(),
            sortino_ratio=self.calculate_sortino_ratio(),
            annual_return_stability=self.calculate_annual_return_stability(),
            cagr=self.calculate_cagr(),
        )
