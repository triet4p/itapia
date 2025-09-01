import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Literal, NamedTuple, Optional, Tuple
import pandas as pd
import numpy as np
from scipy.stats import trim_mean
import math
from abc import ABC, abstractmethod

from app.core.config import PARALLEL_MULTICONTEXT_LIMIT

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

class EvaluateScenario(NamedTuple):
    action_mapper: _BaseActionMapper
    weight: float

class Evaluator(ABC):
    """
    Một interface để thực hiện việc đánh giá một Rule.
    """
    
    def __init__(self, evaluate_scenarios: Optional[List[EvaluateScenario]] = None):
        self.evaluate_scenarios = evaluate_scenarios if evaluate_scenarios else []  
        
    
    def add_evaluate_scenario(self, action_mapper: _BaseActionMapper, weight: float = 1.0):
        self.evaluate_scenarios.append(EvaluateScenario(action_mapper, weight))
        return self

    @abstractmethod
    def evaluate(self, rule: Rule) -> BacktestPerformanceMetrics:
        pass

class SingleContextEvaluator(Evaluator):
    """
    Điều phối quy trình đánh giá một Rule và trích xuất một bộ các giá trị
    mục tiêu (objectives) để phục vụ cho thuật toán tối ưu hóa đa mục tiêu
    như NSGA-II.
    """

    def __init__(self, 
                 context: BacktestContext,
                 evaluate_scenarios: Optional[List[EvaluateScenario]] = None):
        """
        Khởi tạo Evaluator.

        Args:
            context (BacktestContext): Một đối tượng context đã ở trạng thái 'READY',
                                       chứa dữ liệu OHLCV và các báo cáo lịch sử.
        """
        super().__init__(evaluate_scenarios)
        if context.status != 'READY_SERVE':
            raise ValueError(f"Context for '{context.ticker}' is not in 'READY' state. Please load data into memory first.")
            
        self.context = context
        
        # Lấy dữ liệu ra một lần để tái sử dụng trong suốt vòng đời của evaluator
        self.ohlcv_df = self.context.ohlcv_df
        self.historical_reports = self.context.historical_reports
        
    
    def _generate_actions(self, rule: Rule, action_mapper: _BaseActionMapper) -> Dict[datetime, Action]:
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
                action = action_mapper.map_action(
                    score_final=score_result
                )
                if action.action_type != 'HOLD':
                    actions_dict[report_date] = action
            except Exception as e:
                logger.warn(f"Rule execution failed for '{rule.name}' on report date {report_date.date()}. Error: {e}")
                continue
                
        return actions_dict
        
    def _evaluate_each_scenario(self, rule: Rule, scenario: EvaluateScenario) -> BacktestPerformanceMetrics:
        logger.debug(f"Evaluating rule '{rule.name}' for ticker '{self.context.ticker}' with scenario {str(scenario.action_mapper)}...")
        actions_dict = self._generate_actions(rule, scenario.action_mapper)
        # Bước 2: Chạy mô phỏng backtest.
        simulator = BacktestSimulator(self.context.ticker, self.ohlcv_df, actions_dict)
        trade_log = simulator.run()

        # Bước 3: Phân tích kết quả từ nhật ký giao dịch.
        metrics_calculator = PerformanceMetrics(trade_log)
        performance_metrics = metrics_calculator.summary()
        
        logger.debug(f"Rule '{rule.name}' evaluation complete")
        
        return performance_metrics
    
    def _aggerate_obj_from_scenarios(self, 
                                     scenario_results: Dict[EvaluateScenario, BacktestPerformanceMetrics]) -> BacktestPerformanceMetrics:
        final_metrics_dict = BacktestPerformanceMetrics().model_dump()
        total_weight = sum(scenario.weight for scenario in scenario_results.keys())
        
        for scenario, res in scenario_results.items():
            res_dict = res.model_dump()
            
            for attr in final_metrics_dict.keys():
                final_metrics_dict[attr] += res_dict[attr] * scenario.weight / total_weight
                
        return BacktestPerformanceMetrics(
            num_trades=int(final_metrics_dict['num_trades']),
            total_return_pct=final_metrics_dict['total_return_pct'],
            max_drawdown_pct=final_metrics_dict['max_drawdown_pct'],
            win_rate_pct=final_metrics_dict['win_rate_pct'],
            profit_factor=final_metrics_dict['profit_factor'],
            sharpe_ratio=final_metrics_dict['sharpe_ratio'],
            sortino_ratio=final_metrics_dict['sortino_ratio'],
            annual_return_stability=final_metrics_dict['annual_return_stability'],
            cagr=final_metrics_dict['cagr']
        )
            

    def evaluate(self, rule: Rule) -> BacktestPerformanceMetrics:
        """
        Hàm chính: Thực hiện quy trình đánh giá end-to-end cho một Rule.

        Args:
            rule (Rule): Đối tượng Rule cần được đánh giá.

        Returns:
            Tuple[ObjectiveValues, BacktestPerformanceMetrics]: 
                - Một tuple chứa các giá trị mục tiêu đã được chuẩn hóa.
                - Một đối tượng chứa tất cả các chỉ số hiệu suất chi tiết (để lưu trữ).
        """
        if not self.evaluate_scenarios:
            raise ValueError("Requires at least 1 scenarios")
        
        scenario_results: Dict[EvaluateScenario, BacktestPerformanceMetrics] = {}
        for scenario in self.evaluate_scenarios:
            scenario_results[scenario] = self._evaluate_each_scenario(rule, scenario)
        
        return self._aggerate_obj_from_scenarios(scenario_results)
    
class MultiContextEvaluator(Evaluator):
    """
    Điều phối việc đánh giá một Rule duy nhất trên NHIỀU context (tickers) khác nhau,
    sau đó tổng hợp các kết quả thành một vector mục tiêu duy nhất.
    """
    def __init__(self, contexts: List[BacktestContext], 
                 evaluate_scenarios: Optional[List[EvaluateScenario]] = None,
                 aggregation_method: Literal['mean', 'median', 'trim-mean'] = 'median'):
        """
        Khởi tạo evaluator đa luồng.

        Args:
            contexts (List[BacktestContext]): Danh sách tất cả các context đã ở trạng thái 'READY_SERVE'.
            action_mapper (_BaseActionMapper): Instance của chiến lược giao dịch sẽ được sử dụng.
        """
        super().__init__(evaluate_scenarios)
        self.contexts = contexts
        self.semaphore = asyncio.Semaphore(PARALLEL_MULTICONTEXT_LIMIT)
        self.aggregation_method = aggregation_method
        
    def _evaluate_single_context_sync(self, context: BacktestContext, rule: Rule) -> BacktestPerformanceMetrics:
        """
        Hàm đồng bộ (synchronous) để thực thi việc đánh giá trên một context.
        Hàm này sẽ được chạy trong một thread riêng bởi asyncio.to_thread.
        """
        try:
            # 2. Khởi tạo evaluator và chạy đánh giá
            _evaluator = SingleContextEvaluator(context, self.evaluate_scenarios)
            return _evaluator.evaluate(rule)
        except Exception as e:
            logger.warn(f"Evaluation failed for rule '{rule.name}' on ticker '{context.ticker}': {e}")
            # Trả về kết quả tệ nhất nếu có lỗi
            worst_metrics = BacktestPerformanceMetrics()
            return worst_metrics

    async def _evaluate_with_semaphore(self, context: BacktestContext, rule: Rule) -> BacktestPerformanceMetrics:
        """
        Hàm worker bất đồng bộ được kiểm soát bởi semaphore.
        """
        async with self.semaphore:
            # Chờ để có một "slot" trống.
            # Sau khi có slot, chạy tác vụ CPU-bound trong một thread riêng.
            return await asyncio.to_thread(self._evaluate_single_context_sync, context, rule)

    async def evaluate_async(self, rule: Rule) -> BacktestPerformanceMetrics:
        """
        (Bất đồng bộ) Thực thi đánh giá một Rule trên tất cả các context một cách song song
        và trả về một vector mục tiêu đã được tổng hợp.
        """
        if not self.contexts:
            logger.warn("No contexts to evaluate. Returning worst-case fitness.")
            worst_metrics = BacktestPerformanceMetrics()
            return worst_metrics

        logger.info(f"Evaluating rule '{rule.name}' on {len(self.contexts)} tickers with concurrency limit {PARALLEL_MULTICONTEXT_LIMIT}...")

        tasks = [
            self._evaluate_with_semaphore(context, rule)
            for context in self.contexts
        ]
        
        results: List[BacktestPerformanceMetrics] = await asyncio.gather(*tasks)
        
        if not results:
            logger.warn(f"All evaluations failed for rule '{rule.name}'. Returning worst-case fitness.")
            worst_metrics = BacktestPerformanceMetrics()
            return worst_metrics

        metrics_df = pd.DataFrame([m.model_dump() for m in results])
        if self.aggregation_method == 'mean':
            metrics_series = metrics_df.mean()
        elif self.aggregation_method == 'median':
            metrics_series = metrics_df.median()
        else:
            metrics_series = metrics_df.apply(lambda col: trim_mean(col, proportiontocut=0.1))
        metric_dict = metrics_series.to_dict()
        aggregated_metrics = BacktestPerformanceMetrics(
            num_trades=int(metric_dict['num_trades']),
            total_return_pct=metric_dict['total_return_pct'],
            max_drawdown_pct=metric_dict['max_drawdown_pct'],
            win_rate_pct=metric_dict['win_rate_pct'],
            profit_factor=metric_dict['profit_factor'],
            sharpe_ratio=metric_dict['sharpe_ratio'],
            sortino_ratio=metric_dict['sortino_ratio'],
            annual_return_stability=metric_dict['annual_return_stability'],
            cagr=metric_dict['cagr']
        )

        logger.info(f"Rule '{rule.name}' evaluation complete. Aggregated objectives: {aggregated_metrics}")

        return aggregated_metrics
    
    # --- YÊU CẦU 2: WRAPPER ĐỒNG BỘ ---
    def evaluate(self, rule: Rule) -> BacktestPerformanceMetrics:
        """
        (Đồng bộ) Đây là hàm wrapper để gọi từ một môi trường đồng bộ (ví dụ: vòng lặp của thuật toán di truyền).
        Nó sẽ khởi động event loop của asyncio, chạy hàm `evaluate_async`, và trả về kết quả.
        """
        try:
            # Kiểm tra xem có event loop nào đang chạy không
            loop = asyncio.get_running_loop()
            # Nếu có, ta không thể dùng asyncio.run(), phải tạo task và chạy trong loop đó
            # (Trường hợp này phức tạp và ít xảy ra, tạm thời bỏ qua để đơn giản)
            raise RuntimeError("evaluate_sync cannot be called from within a running asyncio event loop.")
        except RuntimeError:
            # Không có event loop nào đang chạy, đây là trường hợp thông thường.
            # asyncio.run() sẽ tự động tạo một loop mới, chạy coroutine cho đến khi xong, và đóng loop.
            return asyncio.run(self.evaluate_async(rule))