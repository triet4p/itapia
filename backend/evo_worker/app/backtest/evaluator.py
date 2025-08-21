from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
import math

# Import các thành phần đã xây dựng
from .context import BacktestContext
from .action import _BaseActionMapper, Action
from .simulator import BacktestSimulator
from .metrics import PerformanceMetrics
from .trade import Trade

# Import các thành phần từ shared library
from itapia_common.rules.rule import Rule
from itapia_common.logger import ITAPIALogger
from itapia_common.schemas.entities.backtest import BacktestPerformanceMetrics

logger = ITAPIALogger('Fitness Evaluator (Multi-Objective)')

# Định nghĩa một kiểu dữ liệu mới để làm cho code rõ ràng hơn
# Đây là "kết quả" mà thuật toán NSGA-II sẽ làm việc
ObjectiveValues = Tuple[float, ...]

class FitnessEvaluator:
    """
    Điều phối quy trình đánh giá một Rule và trích xuất một bộ các giá trị
    mục tiêu (objectives) để phục vụ cho thuật toán tối ưu hóa đa mục tiêu
    như NSGA-II.
    """

    def __init__(self, 
                 context: BacktestContext,
                 action_mapper: _BaseActionMapper):
        """
        Khởi tạo Evaluator.

        Args:
            context (BacktestContext): Một đối tượng context đã ở trạng thái 'READY',
                                       chứa dữ liệu OHLCV và các báo cáo lịch sử.
            action_mapper (_BaseActionMapper): Một instance của chiến lược giao dịch
                                               để ánh xạ tín hiệu thành hành động.
        """
        if context.status != 'READY_SERVE':
            raise ValueError(f"Context for '{context.ticker}' is not in 'READY' state. Please load data into memory first.")
            
        self.context = context
        self.action_mapper = action_mapper
        
        # Lấy dữ liệu ra một lần để tái sử dụng trong suốt vòng đời của evaluator
        self.ohlcv_df = self.context.ohlcv_df
        self.historical_reports = self.context.historical_reports

    def evaluate(self, rule: Rule) -> Tuple[ObjectiveValues, BacktestPerformanceMetrics]:
        """
        Hàm chính: Thực hiện quy trình đánh giá end-to-end cho một Rule.

        Args:
            rule (Rule): Đối tượng Rule cần được đánh giá.

        Returns:
            Tuple[ObjectiveValues, BacktestPerformanceMetrics]: 
                - Một tuple chứa các giá trị mục tiêu đã được chuẩn hóa.
                - Một đối tượng chứa tất cả các chỉ số hiệu suất chi tiết (để lưu trữ).
        """
        logger.debug(f"Evaluating rule '{rule.name}' for ticker '{self.context.ticker}'...")
        
        # Bước 1: Tạo dictionary các hành động giao dịch từ Rule.
        actions_dict = self._generate_actions_from_rule(rule)

        # Bước 2: Chạy mô phỏng backtest.
        simulator = BacktestSimulator(self.context.ticker, self.ohlcv_df, actions_dict)
        trade_log = simulator.run()

        # Bước 3: Phân tích kết quả từ nhật ký giao dịch.
        metrics_calculator = PerformanceMetrics(trade_log)
        performance_metrics = metrics_calculator.summary()

        # Bước 4: Trích xuất và chuẩn hóa các giá trị mục tiêu.
        objectives = self._extract_and_normalize_objectives(performance_metrics)
        
        logger.debug(f"Rule '{rule.name}' evaluation complete. Objectives: {objectives}")
        
        return objectives, performance_metrics

    def _generate_actions_from_rule(self, rule: Rule) -> Dict[datetime, Action]:
        """
        Hàm hỗ trợ: Lặp qua các báo cáo lịch sử, thực thi Rule, và
        sử dụng ActionMapper để tạo ra một dictionary các hành động.
        """
        actions_dict: Dict[datetime, Action] = {}
        start_date, end_date = self.ohlcv_df.index.min(), self.ohlcv_df.index.max()

        for report in self.historical_reports:
            report_date = datetime.fromtimestamp(report.generated_timestamp, tz=timezone.utc)
            if not (start_date <= report_date <= end_date):
                continue
            try:
                score_result = rule.execute(report)
                action = self.action_mapper.map_action(
                    score_final=score_result,
                    purpose=rule.purpose
                )
                if action.action_type != 'HOLD':
                    actions_dict[report_date] = action
            except Exception as e:
                logger.warn(f"Rule execution failed for '{rule.name}' on report date {report_date.date()}. Error: {e}")
                continue
                
        return actions_dict

    def _extract_and_normalize_objectives(self, metrics: BacktestPerformanceMetrics) -> ObjectiveValues:
        """
        Hàm cốt lõi của NSGA-II: Trích xuất các chỉ số và chuẩn hóa chúng
        theo quy tắc "càng cao càng tốt".
        
        Thứ tự của các mục tiêu trong tuple trả về phải luôn không đổi.
        """
        # --- Trường hợp cơ sở: Rule không tạo ra giao dịch nào ---
        # Trả về kết quả tệ nhất có thể cho tất cả các mục tiêu.
        if metrics.num_trades == 0:
            return (
                0.0,  # total_return_pct
                0.0,  # sharpe_ratio
                0.0,  # resilience (1.0 - max_drawdown_pct)
                0.0,  # win_rate_pct
                0.0,  # profit_factor
                0.0   # num_trades
            )

        # --- Chuẩn hóa các mục tiêu ---

        # Mục tiêu 1: Tổng lợi nhuận. Đã theo hướng "càng cao càng tốt".
        # Giới hạn giá trị tối thiểu là -1 (-100%) để tránh số âm quá lớn.
        obj_total_return = max(-1.0, metrics.total_return_pct)

        # Mục tiêu 2: Tỷ lệ Sharpe. Giá trị âm không tốt, coi là 0.
        obj_sharpe_ratio = max(0.0, metrics.sharpe_ratio)
        
        # Mục tiêu 3: Khả năng chịu đựng (Resilience).
        # max_drawdown_pct (càng thấp càng tốt) -> 1 - max_drawdown_pct (càng cao càng tốt).
        obj_resilience = 1.0 - metrics.max_drawdown_pct
        
        # Mục tiêu 4: Tỷ lệ thắng. Đã ở thang 0-1, "càng cao càng tốt".
        obj_win_rate = metrics.win_rate_pct
        
        # Mục tiêu 5: Hệ số lợi nhuận. Giá trị < 1 là tệ.
        # Dùng log(max(1, x)) để các giá trị > 1 được thưởng và < 1 không bị phạt âm.
        obj_profit_factor = math.log(max(1.0, metrics.profit_factor))
        
        # Mục tiêu 6: Số lượng giao dịch.
        # Đây có thể là một mục tiêu phụ, nhưng hữu ích để tránh các rule chỉ thắng 1 trade.
        obj_num_trades = float(metrics.num_trades)

        # Trả về một tuple chứa các giá trị mục tiêu theo một thứ tự cố định.
        # Thuật toán NSGA-II sẽ sử dụng tuple này để so sánh các rule.
        objectives = (
            obj_total_return,
            obj_sharpe_ratio,
            obj_resilience,
            obj_win_rate,
            obj_profit_factor,
            obj_num_trades
        )
        
        # Đảm bảo tất cả các giá trị đều là số hữu hạn
        if not all(np.isfinite(obj) for obj in objectives):
            # Nếu có lỗi (ví dụ: profit_factor là inf), trả về tuple tệ nhất
            return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
            
        return objectives