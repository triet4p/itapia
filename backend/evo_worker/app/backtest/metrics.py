import pandas as pd
import numpy as np
from typing import List, Dict, Optional

from .trade import Trade

from itapia_common.schemas.entities.backtest import BacktestPerformanceMetrics

class PerformanceMetrics:
    """
    Phân tích một nhật ký giao dịch (trade log) và tính toán ra các
    chỉ số hiệu suất và rủi ro chính.
    """
    def __init__(self, 
                 trade_log: List[Trade], 
                 initial_capital: float = 100000.0,
                 risk_free_rate_annual: float = 0.02): # Tỷ lệ phi rủi ro 2%/năm
        """
        Khởi tạo nhà phân tích.
        
        Args:
            trade_log (List[Trade]): Danh sách các giao dịch đã hoàn thành từ Simulator.
            initial_capital (float): Vốn khởi điểm để tính toán equity curve.
            risk_free_rate_annual (float): Tỷ lệ lợi nhuận phi rủi ro hàng năm để tính Sharpe Ratio.
        """
        if not trade_log:
            # Nếu không có giao dịch nào, khởi tạo với trạng thái trống
            self.trade_log = []
            self.trades_df = pd.DataFrame()
        else:
            self.trade_log = trade_log
            # Chuyển trade log thành DataFrame để dễ dàng tính toán vector hóa
            self.trades_df = self._create_trades_dataframe()

        self.initial_capital = initial_capital
        self.risk_free_rate_daily = (1 + risk_free_rate_annual)**(1/252) - 1 # 252 ngày giao dịch/năm

        # Các thuộc tính sẽ được tính toán "lười" (lazy calculation)
        self._equity_curve: Optional[pd.Series] = None

    def _create_trades_dataframe(self) -> pd.DataFrame:
        """Chuyển đổi list of Trade objects thành một DataFrame."""
        df = pd.DataFrame(self.trade_log)
        df['profit_pct'] = np.array([trade.profit_pct for trade in self.trade_log])
        df['duration_days'] = np.array([trade.duration_days for trade in self.trade_log])
        # Chuyển đổi ngày tháng thành kiểu datetime để có thể sắp xếp
        df['exit_date'] = pd.to_datetime(df['exit_date'])
        df.set_index('exit_date', inplace=True, drop=False)
        df.sort_index(inplace=True)
        return df

    def calculate_equity_curve(self) -> pd.Series:
        """
        Tính toán đường cong vốn (equity curve) dựa trên kết quả giao dịch.
        Đường cong vốn thể hiện sự thay đổi của tài khoản theo thời gian.
        """
        if self._equity_curve is not None:
            return self._equity_curve

        if self.trades_df.empty:
            self._equity_curve = pd.Series([self.initial_capital])
            return self._equity_curve

        # Tính toán lợi nhuận/thua lỗ của mỗi giao dịch dựa trên % vốn
        self.trades_df['return_pct'] = self.trades_df['profit_pct'] * self.trades_df['position_size_pct']
        
        # (1 + return_pct) là hệ số tăng trưởng
        self.trades_df['growth_factor'] = 1 + self.trades_df['return_pct']
        
        # Tính toán giá trị tài khoản sau mỗi giao dịch
        self.trades_df['equity'] = self.initial_capital * self.trades_df['growth_factor'].cumprod()
        
        # Tạo equity curve hoàn chỉnh
        equity_curve = pd.Series(self.initial_capital, index=[self.trades_df.index.min() - pd.Timedelta(days=1)])
        equity_curve = pd.concat([equity_curve, self.trades_df['equity']])
        
        self._equity_curve = equity_curve
        return self._equity_curve

    def calculate_total_return(self) -> float:
        """Tính tổng lợi nhuận (%) của toàn bộ chuỗi giao dịch."""
        if self.trades_df.empty:
            return 0.0
        
        equity_curve = self.calculate_equity_curve()
        final_equity = equity_curve.iloc[-1]
        return (final_equity - self.initial_capital) / self.initial_capital

    def calculate_max_drawdown(self) -> float:
        """
        Tính mức sụt giảm tài khoản lớn nhất (Max Drawdown).
        Đây là một chỉ số rủi ro quan trọng, cho thấy mức lỗ tối đa từ đỉnh.
        """
        if self.trades_df.empty:
            return 0.0
        
        equity_curve = self.calculate_equity_curve()
        # Tính "đỉnh" cao nhất từ trước đến nay
        running_max = equity_curve.cummax()
        # Tính % sụt giảm từ đỉnh tại mỗi điểm
        drawdown = (equity_curve - running_max) / running_max
        return abs(drawdown.min())

    def calculate_win_rate(self) -> float:
        """Tính tỷ lệ phần trăm các giao dịch có lời."""
        if self.trades_df.empty:
            return 0.0
            
        winning_trades = self.trades_df[self.trades_df['profit_pct'] > 0]
        return len(winning_trades) / len(self.trades_df)

    # Mở file evo-worker/app/backtest/metrics.py và thay thế hàm này

    def calculate_profit_factor(self) -> float:
        """
        Tính toán Profit Factor.
        (Tổng % lợi nhuận từ các giao dịch thắng) / (Tổng % thua lỗ từ các giao dịch thua).
        Phiên bản này hoạt động trực tiếp trên `profit_pct` để tránh các lỗi reindex phức tạp.
        """
        if self.trades_df.empty:
            return 0.0
        
        # Lấy cột profit_pct đã được tính toán và xác thực
        trade_returns = self.trades_df['profit_pct']
        
        # Tính tổng % lợi nhuận từ tất cả các giao dịch thắng
        gross_profit = trade_returns[trade_returns > 0].sum()
        
        # Tính tổng % thua lỗ từ tất cả các giao dịch thua
        gross_loss = abs(trade_returns[trade_returns < 0].sum())
        
        # Xử lý trường hợp không có giao dịch thua nào
        if gross_loss == 0:
            if gross_profit > 0:
                # Nếu không có lỗ nhưng có lời, profit factor là vô hạn.
                # Trả về một số lớn, dương để thể hiện kết quả rất tốt.
                return 9999.0
            else:
                # Không lời, không lỗ (tất cả các trade đều hòa vốn).
                # Profit factor không xác định, trả về 1.0 (hòa vốn).
                return 1.0
        
        return gross_profit / gross_loss

    def calculate_sharpe_ratio(self) -> float:
        """
        Tính toán Tỷ lệ Sharpe.
        Đo lường lợi nhuận đã điều chỉnh theo rủi ro (độ biến động).
        Giá trị càng cao càng tốt.
        """
        if self.trades_df.empty or len(self.trades_df) < 2:
            return 0.0
            
        # Tính toán tỷ suất sinh lời hàng ngày của danh mục
        equity_curve = self.calculate_equity_curve()
        daily_returns = equity_curve.pct_change().dropna()
        
        if daily_returns.std() == 0:
            return 0.0 # Tránh lỗi chia cho 0
            
        # Lợi nhuận vượt trội so với tỷ lệ phi rủi ro
        excess_returns = daily_returns - self.risk_free_rate_daily
        
        # (Lợi nhuận trung bình / Độ lệch chuẩn) * sqrt(252) để ra Tỷ lệ Sharpe hàng năm
        sharpe_ratio = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)
        return sharpe_ratio
    
    def calculate_sortino_ratio(self, target_return_pct: float = 0.0) -> float:
        """
        Tính toán Tỷ lệ Sortino dựa trên lợi nhuận của TỪNG GIAO DỊCH để có kết quả bền bỉ.

        Args:
            target_return_pct (float): Tỷ lệ lợi nhuận mục tiêu cho mỗi giao dịch. Mặc định là 0.

        Returns:
            float: Tỷ lệ Sortino (không thường niên hóa, vì nó dựa trên giao dịch).
        """
        if self.trades_df.empty or len(self.trades_df) < 2:
            return 0.0

        trade_returns = self.trades_df['profit_pct']

        # 1. Tính lợi nhuận trung bình cho mỗi giao dịch (Tử số)
        avg_return_per_trade = trade_returns.mean()
        
        # 2. Tính Downside Deviation dựa trên các giao dịch thua lỗ (Mẫu số)
        returns_below_target = trade_returns[trade_returns < target_return_pct]
        
        if returns_below_target.empty:
            # Nếu không có giao dịch nào thua lỗ
            return 9999.0 if avg_return_per_trade > 0 else 0.0

        # Tính độ lệch chuẩn của các giao dịch thua lỗ
        downside_deviation = returns_below_target.std()

        if downside_deviation == 0:
            # Trường hợp hiếm gặp (tất cả các lệnh thua đều có cùng một mức lỗ)
            # Hoặc chỉ có 1 lệnh thua
            return 9999.0 if avg_return_per_trade > 0 else 0.0
        
        # 3. Tính toán Sortino Ratio
        sortino_ratio = (avg_return_per_trade - target_return_pct) / downside_deviation
        
        # Không cần thường niên hóa vì nó dựa trên sự kiện (mỗi giao dịch), không phải thời gian.
        return sortino_ratio if np.isfinite(sortino_ratio) else 0.0
    
    def calculate_annual_return_stability(self) -> float:
        """
        Đo lường sự ổn định của lợi nhuận qua các năm.
        Trả về độ lệch chuẩn của lợi nhuận hàng năm. Càng thấp càng tốt.
        """
        if self.trades_df.empty:
            return 999
        
        # Đảm bảo cột return_pct tồn tại
        if 'return_pct' not in self.trades_df.columns:
            self.trades_df['return_pct'] = self.trades_df['profit_pct'] * self.trades_df['position_size_pct']

        # Nhóm các giao dịch theo năm và tính tổng lợi nhuận
        # Lưu ý: Đây là phép cộng đơn giản, không phải lợi nhuận kép, để đánh giá hiệu suất thô
        annual_returns = self.trades_df['return_pct'].resample('YE').sum()
        
        if len(annual_returns) < 2:
            # Thay vì trả về 0.0 (hoàn hảo), hãy kiểm tra xem khoảng thời gian
            # thực tế của các giao dịch có kéo dài hơn một năm không.
            if not self.trades_df.empty:
                trade_duration = self.trades_df.index.max() - self.trades_df.index.min()
                if trade_duration.days < 365:
                    # Nếu chiến lược chỉ tồn tại dưới 1 năm, nó không ổn định.
                    # Trả về một giá trị phạt lớn. 1.0 là một độ lệch chuẩn rất cao.
                    return 1.0 
            
            return 0.02
            
        return annual_returns.std(ddof=0)
    
    def calculate_cagr(self) -> float:
        """
        Tính toán Tỷ lệ Tăng trưởng Kép Hàng năm (CAGR).
        """
        if self.trades_df.empty:
            return 0.0
            
        equity_curve = self.calculate_equity_curve()
        final_equity = equity_curve.iloc[-1]
        
        start_date = equity_curve.index.min()
        end_date = equity_curve.index.max()
        num_days = (end_date - start_date).days
        
        # Nếu thời gian dưới 1 năm, không tính CAGR, trả về total return
        if num_days < 365:
            return self.calculate_total_return()
            
        num_years = num_days / 365.25
        
        cagr = (final_equity / self.initial_capital)**(1 / num_years) - 1
        return cagr

    def summary(self) -> BacktestPerformanceMetrics:
        """
        Tổng hợp tất cả các chỉ số hiệu suất vào một dictionary.
        """
        if self.trades_df.empty:
            return BacktestPerformanceMetrics()

        return BacktestPerformanceMetrics(
            num_trades = len(self.trade_log),
            total_return_pct = self.calculate_total_return(),
            max_drawdown_pct = self.calculate_max_drawdown(),
            win_rate_pct = self.calculate_win_rate(),
            profit_factor = self.calculate_profit_factor(),
            sharpe_ratio = self.calculate_sharpe_ratio(),
            sortino_ratio = self.calculate_sortino_ratio(),
            annual_return_stability=self.calculate_annual_return_stability(),
            cagr=self.calculate_cagr()
        )