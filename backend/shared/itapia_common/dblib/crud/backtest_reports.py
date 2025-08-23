"""This module provides CRUD operations for backtest reports in the database.

It uses SQLAlchemy ORM and text-based SQL queries. The table name is retrieved
from db_config.ANALYSIS_REPORTS_TABLE_NAME. Key functionalities include saving
reports with UPSERT logic and retrieving the latest report before a specified date.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import itapia_common.dblib.db_config as dbcfg
 
class BacktestReportCRUD:
    """CRUD operations for backtest reports in the database."""
    
    def __init__(self, db_session: Session):
        """Initialize the CRUD instance with a database session.

        Args:
            db_session (Session): The SQLAlchemy database session.
        """
        self.db = db_session

    def save_report(self, data: Dict[str, Any]):
        """Save an analysis report to the database using UPSERT logic.

        This method inserts a new report or updates an existing one based on the report_id.
        It uses PostgreSQL's ON CONFLICT DO UPDATE feature for efficient upsert operations.

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

    def get_latest_report_before_date(self, ticker: str, backtest_date: Any):
        """Retrieve the latest analysis report for a given ticker on or before a specific date.

        This method finds the most recent report for a ticker that was created on or before
        the specified date.

        Args:
            ticker (str): The ticker symbol to search for.
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
        result = self.db.execute(stmt, {'ticker': ticker, 'backtest_date': backtest_date})
        if result is not None:
            return result.mappings().one()
        return None
    
    def get_reports_by_ticker(self, ticker: str):
        """Retrieve all analysis reports for a given ticker, ordered by date descending.

        Args:
            ticker (str): The ticker symbol to retrieve reports for.

        Returns:
            List[Dict[str, Any]]: A list of report dictionaries ordered by backtest_date DESC.
        """
        stmt = text(f"""
            SELECT report_id, ticker, backtest_date, report FROM {dbcfg.ANALYSIS_REPORTS_TABLE_NAME}
            WHERE ticker = :ticker
            ORDER BY backtest_date DESC
        """)
        result = self.db.execute(stmt, {'ticker': ticker})
        return result.mappings().all()