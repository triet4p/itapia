# common/dblib/services/backtest_reports.py
"""Service layer for managing backtest reports.

This module provides a high-level interface for saving and retrieving backtest reports,
handling the conversion between Pydantic models and database representations.
"""

import uuid
import json
from datetime import datetime

from sqlalchemy.orm import Session
from itapia_common.schemas.entities.analysis import QuickCheckAnalysisReport
from typing import List, Optional
from itapia_common.dblib.crud.backtest_reports import BacktestReportCRUD

class BacktestReportService:
    """Service for managing backtest reports in the database."""
    
    def __init__(self, db_session: Session):
        self.crud = BacktestReportCRUD(db_session)

    def save_quick_check_report(self, report: QuickCheckAnalysisReport,
                                backtest_date: datetime) -> str:
        """Process and save a QuickCheckAnalysisReport.

        This method converts the Pydantic model to a database-compatible format
        and stores it using the CRUD layer.

        Args:
            report (QuickCheckAnalysisReport): The Pydantic model instance of the report.
            backtest_date (datetime): The backtest date for the report.

        Returns:
            str: The ID of the saved report.
        """
        report_id = f'{report.ticker.upper()}_{backtest_date.strftime("%Y-%m-%d")}'

        data_to_save = {
            'report_id': report_id,
            'backtest_date': backtest_date,
            'ticker': report.ticker,
            'report': json.dumps(report.model_dump(mode='json'))
        }
        
        self.crud.save_report(data_to_save)
        return report_id

    def get_backtest_report(self, ticker: str, backtest_date: datetime) -> Optional[QuickCheckAnalysisReport]:
        """Retrieve the latest QuickCheckAnalysisReport for a ticker on or before a given date.

        If no report is found for the exact date, it fetches the most recent one before it.

        Args:
            ticker (str): The ticker symbol.
            backtest_date (datetime): The date to search from.

        Returns:
            Optional[QuickCheckAnalysisReport]: The report object, or None if not found.
        """
        report_data = self.crud.get_latest_report_before_date(ticker, backtest_date)

        if not report_data:
            return None

        # The 'report' column is a JSONB string, which needs to be parsed.
        report_dict = report_data['report']

        return QuickCheckAnalysisReport.model_validate(report_dict)
    
    def get_all_backtest_reports(self, ticker: str) -> List[QuickCheckAnalysisReport]:
        """Retrieve all backtest reports for a given ticker.

        Args:
            ticker (str): The ticker symbol.

        Returns:
            List[QuickCheckAnalysisReport]: A list of report objects.
        """
        report_datas = self.crud.get_reports_by_ticker(ticker)
        reports = []
        for report_data in report_datas:
            # The 'report' column is a JSONB string, which needs to be parsed.
            report_dict = report_data['report']
            report = QuickCheckAnalysisReport.model_validate(report_dict)
        
            reports.append(report)
            
        return reports