from datetime import datetime

from itapia_common.dblib.services import BacktestReportService
from itapia_common.schemas.entities.analysis import QuickCheckAnalysisReport


class BacktestOrchestrator:
    def __init__(self, backtest_report_service: BacktestReportService):
        self.backtest_report_service = backtest_report_service

    def save_report(self, report: QuickCheckAnalysisReport, backtest_date: datetime):
        self.backtest_report_service.save_quick_check_report(report, backtest_date)
