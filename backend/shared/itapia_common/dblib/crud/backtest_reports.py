# common/dblib/crud/analysis.py
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import itapia_common.dblib.db_config as dbcfg

class BacktestReportCRUD:
    def __init__(self, db_session: Session):
        self.db = db_session

    def save_report(self, data: Dict[str, Any]):
        """
        Saves an analysis report to the database using UPSERT.

        Args:
            data (Dict[str, Any]): A dictionary containing the report data.
                                   Expected keys: 'report_id', 'ticker',
                                   'backtest_date', 'report'.
        """
        stmt = text(f"""
            INSERT INTO {dbcfg.ANALYSIS_REPORTS_TABLE_NAME} (report_id, ticker, backtest_date, report)
            VALUES (:report_id, :ticker, :backtest_date, :report)
            ON CONFLICT (report_id) DO UPDATE SET
                ticker = EXCLUDED.ticker,
                backtest_date = EXCLUDED.backtest_date,
                report = EXCLUDED.report
        """)
        
        self.db.execute(stmt, data)
        self.db.commit()

    def get_latest_report_before_date(self, ticker: str, backtest_date: Any) -> Optional[Dict[str, Any]]:
        """
        Retrieves the latest analysis report for a given ticker on or before a specific date.

        Args:
            ticker (str): The ticker symbol.
            backtest_date (Any): The date to look for reports on or before.

        Returns:
            Optional[Dict[str, Any]]: The report data as a dictionary, or None if not found.
        """
        stmt = text(f"""
            SELECT report_id, ticker, backtest_date, report FROM {dbcfg.ANALYSIS_REPORTS_TABLE_NAME}
            WHERE ticker = :ticker AND backtest_date <= :backtest_date
            ORDER BY backtest_date DESC
            LIMIT 1
        """)
        result = self.db.execute(stmt, {'ticker': ticker, 'backtest_date': backtest_date}).first()
        return dict(result._mapping) if result else None