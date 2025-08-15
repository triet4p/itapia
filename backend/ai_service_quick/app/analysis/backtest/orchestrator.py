from datetime import datetime, timezone
from typing import List
import pandas as pd

import app.core.config as cfg

from itapia_common.dblib.services import BacktestReportService    
from itapia_common.schemas.entities.analysis import QuickCheckAnalysisReport


class BacktestOrchestrator:
    def __init__(self, 
                 backtest_report_service: BacktestReportService):
        self.backtest_report_service = backtest_report_service
        self.backtest_dates: List[datetime] = []
        
    def add_backtest_date(self, backtest_date: datetime):
        self.backtest_dates.append(backtest_date)
        
    def add_backtest_dates_from_cfg(self):
        for year in range(cfg.BACKTEST_START_YEAR, cfg.BACKTEST_END_YEAR + 1):
            for month in range(1, 13):
                self.backtest_dates.append(datetime(year, month, cfg.BACKTEST_DAY_OF_MONTH, tzinfo=timezone.utc))

    def save_report(self, report: QuickCheckAnalysisReport,
                    backtest_date: datetime):
        self.backtest_report_service.save_quick_check_report(report, backtest_date)
        
    def select_backtest_datas(self, daily_df: pd.DataFrame) -> pd.DataFrame:
        # Select best rows match to each backtest_date
        backtest_datas = []
        for backtest_date in self.backtest_dates:
            before_datas = daily_df[daily_df.index <= pd.to_datetime(backtest_date, utc=True)]
            if not before_datas.empty:
                backtest_datas.append(before_datas.iloc[-1])
        return pd.DataFrame(backtest_datas)
    
        