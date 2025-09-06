"""Fitness evaluator for multi-objective optimization of forecasting rules."""

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

# Import the components that have been built
from .context import BacktestContext
from .action import _BaseActionMapper, Action
from .simulator import BacktestSimulator
from .metrics import PerformanceMetrics
from .trade import Trade

# Import components from shared library
from itapia_common.rules.rule import Rule
from itapia_common.logger import ITAPIALogger
from itapia_common.schemas.entities.backtest import BacktestPerformanceMetrics

logger = ITAPIALogger('Fitness Evaluator (Multi-Objective)')

# Define a new data type to make the code clearer
# This is the "result" that the NSGA-II algorithm will work with


class EvaluateScenario(NamedTuple):
    """Represents an evaluation scenario with action mapper and weight."""
    action_mapper: _BaseActionMapper
    weight: float


class Evaluator(ABC):
    """Interface for evaluating a Rule."""
    
    def __init__(self, evaluate_scenarios: Optional[List[EvaluateScenario]] = None):
        """Initialize evaluator with evaluation scenarios.
        
        Args:
            evaluate_scenarios (Optional[List[EvaluateScenario]], optional): List of evaluation scenarios. 
                Defaults to None.
        """
        self.evaluate_scenarios = evaluate_scenarios if evaluate_scenarios else []  
        
    
    def add_evaluate_scenario(self, action_mapper: _BaseActionMapper, weight: float = 1.0):
        """Add an evaluation scenario to the evaluator.
        
        Args:
            action_mapper (_BaseActionMapper): Action mapper for the scenario
            weight (float, optional): Weight for the scenario. Defaults to 1.0.
            
        Returns:
            Self: Returns self for method chaining
        """
        self.evaluate_scenarios.append(EvaluateScenario(action_mapper, weight))
        return self

    @abstractmethod
    def evaluate(self, rule: Rule) -> BacktestPerformanceMetrics:
        """Abstract method to evaluate a rule.
        
        Args:
            rule (Rule): Rule to evaluate
            
        Returns:
            BacktestPerformanceMetrics: Performance metrics for the rule
        """
        pass


class SingleContextEvaluator(Evaluator):

    def __init__(self, 
                 context: BacktestContext,
                 evaluate_scenarios: Optional[List[EvaluateScenario]] = None):
        """Initialize Evaluator.
        
        Args:
            context (BacktestContext): A context object in 'READY' state,
                                       containing OHLCV data and historical reports.
            evaluate_scenarios (Optional[List[EvaluateScenario]], optional): List of evaluation scenarios. 
                Defaults to None.
        """
        super().__init__(evaluate_scenarios)
        if context.status != 'READY_SERVE':
            raise ValueError(f"Context for '{context.ticker}' is not in 'READY' state. Please load data into memory first.")
            
        self.context = context
        
        # Extract data once for reuse throughout the evaluator's lifecycle
        self.ohlcv_df = self.context.ohlcv_df
        self.historical_reports = self.context.historical_reports
        
    
    def _generate_actions(self, rule: Rule, action_mapper: _BaseActionMapper) -> Dict[datetime, Action]:
        """Helper function: Iterate through historical reports, execute Rule, and
        use ActionMapper to generate a dictionary of actions.
        
        Args:
            rule (Rule): Rule to execute
            action_mapper (_BaseActionMapper): Action mapper to use
            
        Returns:
            Dict[datetime, Action]: Dictionary of actions indexed by datetime
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
        """Evaluate a rule for a specific scenario.
        
        Args:
            rule (Rule): Rule to evaluate
            scenario (EvaluateScenario): Scenario to evaluate with
            
        Returns:
            BacktestPerformanceMetrics: Performance metrics for the scenario
        """
        logger.debug(f"Evaluating rule '{rule.name}' for ticker '{self.context.ticker}' with scenario {str(scenario.action_mapper)}...")
        actions_dict = self._generate_actions(rule, scenario.action_mapper)
        # Step 2: Run backtest simulation.
        simulator = BacktestSimulator(self.context.ticker, self.ohlcv_df, actions_dict)
        trade_log = simulator.run()

        # Step 3: Analyze results from trade log.
        metrics_calculator = PerformanceMetrics(trade_log)
        performance_metrics = metrics_calculator.summary()
        
        logger.debug(f"Rule '{rule.name}' evaluation complete")
        
        return performance_metrics
    
    def _aggerate_obj_from_scenarios(self, 
                                     scenario_results: Dict[EvaluateScenario, BacktestPerformanceMetrics]) -> BacktestPerformanceMetrics:
        """Aggregate objectives from multiple scenarios.
        
        Args:
            scenario_results (Dict[EvaluateScenario, BacktestPerformanceMetrics]): Results from each scenario
            
        Returns:
            BacktestPerformanceMetrics: Aggregated performance metrics
        """
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
        """Main function: Execute end-to-end evaluation process for a Rule.
        
        Args:
            rule (Rule): Rule object to evaluate.
            
        Returns:
            BacktestPerformanceMetrisc: An object containing all detailed performance metrics (for storage).
                
        Raises:
            ValueError: If no evaluation scenarios are provided
        """
        if not self.evaluate_scenarios:
            raise ValueError("Requires at least 1 scenarios")
        
        scenario_results: Dict[EvaluateScenario, BacktestPerformanceMetrics] = {}
        for scenario in self.evaluate_scenarios:
            scenario_results[scenario] = self._evaluate_each_scenario(rule, scenario)
        
        return self._aggerate_obj_from_scenarios(scenario_results)
    
class MultiContextEvaluator(Evaluator):
    """Coordinates the evaluation of a single Rule on MULTIPLE contexts (tickers),
    then aggregates the results into a single target vector.
    """
    def __init__(self, contexts: List[BacktestContext], 
                 evaluate_scenarios: Optional[List[EvaluateScenario]] = None,
                 aggregation_method: Literal['mean', 'median', 'trim-mean'] = 'median'):
        """
        Initialize multi-threaded evaluator.
        
        Args:
            contexts (List[BacktestContext]): List of all contexts in 'READY_SERVE' state.
            evaluate_scenarios (Optional[List[EvaluateScenario]], optional): List of evaluation scenarios. 
                Defaults to None.
            aggregation_method (Literal[&#39;mean&#39;, &#39;median&#39;, &#39;trim, optional): Aggeration method use to combine
                results from all contexts. Defaults to 'median'.
        """
        super().__init__(evaluate_scenarios)
        self.contexts = contexts
        self.semaphore = asyncio.Semaphore(PARALLEL_MULTICONTEXT_LIMIT)
        self.aggregation_method = aggregation_method
        
    def _evaluate_single_context_sync(self, context: BacktestContext, rule: Rule) -> BacktestPerformanceMetrics:
        """Synchronous function to execute evaluation on a single context.
        
        This function will run in a separate thread by asyncio.to_thread.
        
        Args:
            context (BacktestContext): Context to evaluate
            rule (Rule): Rule to evaluate
            
        Returns:
            BacktestPerformanceMetrics: Performance metrics for the context
        """
        try:
            # 2. Initialize evaluator and run evaluation
            _evaluator = SingleContextEvaluator(context, self.evaluate_scenarios)
            return _evaluator.evaluate(rule)
        except Exception as e:
            logger.warn(f"Evaluation failed for rule '{rule.name}' on ticker '{context.ticker}': {e}")
            # Return worst-case result if there's an error
            worst_metrics = BacktestPerformanceMetrics()
            return worst_metrics

    async def _evaluate_with_semaphore(self, context: BacktestContext, rule: Rule) -> BacktestPerformanceMetrics:
        """Asynchronous worker function controlled by semaphore.
        
        Args:
            context (BacktestContext): Context to evaluate
            rule (Rule): Rule to evaluate
            
        Returns:
            BacktestPerformanceMetrics: Performance metrics for the context
        """
        async with self.semaphore:
            # Wait for an available "slot".
            # After getting a slot, run the CPU-bound task in a separate thread.
            return await asyncio.to_thread(self._evaluate_single_context_sync, context, rule)

    async def evaluate_async(self, rule: Rule) -> BacktestPerformanceMetrics:
        """(Asynchronous) Execute evaluation of a Rule on all contexts in parallel
        and return an aggregated target vector.
        
        Args:
            rule (Rule): Rule to evaluate
            
        Returns:
            BacktestPerformanceMetrics: Aggregated performance metrics
            
        Raises:
            Exception: If all evaluations fail
        """
        if not self.contexts:
            logger.warn("No contexts to evaluate. Returning worst-case fitness.")
            worst_metrics = BacktestPerformanceMetrics()
            return worst_metrics

        logger.debug(f"Evaluating rule '{rule.name}' on {len(self.contexts)} tickers with concurrency limit {PARALLEL_MULTICONTEXT_LIMIT}...")

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

        logger.debug(f"Rule '{rule.name}' evaluation complete. Aggregated objectives: {aggregated_metrics}")

        return aggregated_metrics
    
    # --- REQUIREMENT 2: SYNCHRONOUS WRAPPER ---
    def evaluate(self, rule: Rule) -> BacktestPerformanceMetrics:
        """(Synchronous) This is a wrapper function to call from a synchronous environment 
        (e.g., genetic algorithm loop).
        
        It will start the asyncio event loop, run the `evaluate_async` function, and return the result.
        
        Args:
            rule (Rule): Rule to evaluate
            
        Returns:
            BacktestPerformanceMetrics: Aggregated performance metrics
            
        Raises:
            RuntimeError: If called from within a running asyncio event loop
        """
        try:
            # Check if there's a running event loop
            loop = asyncio.get_running_loop()
            # If there is, we can't use asyncio.run(), must create a task and run it in that loop
            # (This case is complex and rare, temporarily ignored for simplicity)
            raise RuntimeError("evaluate_sync cannot be called from within a running asyncio event loop.")
        except RuntimeError:
            # No running event loop, this is the normal case.
            # asyncio.run() will automatically create a new loop, run the coroutine until completion, and close the loop.
            return asyncio.run(self.evaluate_async(rule))