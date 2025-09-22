"""This module provides CRUD operations for backtest reports in the database.

It uses SQLAlchemy ORM and text-based SQL queries. The table name is retrieved
from db_config.ANALYSIS_REPORTS_TABLE_NAME. Key functionalities include saving
reports with UPSERT logic and retrieving the latest report before a specified date.
"""

from typing import Any, Dict, Optional

import itapia_common.dblib.db_config as dbcfg
from sqlalchemy import RowMapping, Sequence, text
from sqlalchemy.orm import Session


class BacktestReportCRUD:
    """CRUD operations for backtest reports in the database."""

    def __init__(self, db_session: Session):
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
        stmt = text(
            f"""
            INSERT INTO public.{dbcfg.ANALYSIS_REPORTS_TABLE_NAME} (report_id, ticker, backtest_date, report)
            VALUES (:report_id, :ticker, :backtest_date, :report)
            ON CONFLICT (report_id) DO UPDATE SET
                ticker = EXCLUDED.ticker,
                backtest_date = EXCLUDED.backtest_date,
                report = EXCLUDED.report
        """
        )

        self.db.execute(stmt, data)
        self.db.commit()

    def get_latest_report_before_date(
        self, ticker: str, backtest_date: Any
    ) -> Optional[RowMapping]:
        stmt = text(
            f"""
            SELECT report_id, ticker, backtest_date, report FROM public.{dbcfg.ANALYSIS_REPORTS_TABLE_NAME}
            WHERE ticker = :ticker AND backtest_date <= :backtest_date
            ORDER BY backtest_date DESC
            LIMIT 1
        """
        )
        result = self.db.execute(
            stmt, {"ticker": ticker, "backtest_date": backtest_date}
        )
        if result is not None:
            return result.mappings().one()
        return None

    def get_reports_by_ticker(self, ticker: str) -> Sequence[RowMapping]:
        stmt = text(
            f"""
            SELECT report_id, ticker, backtest_date, report FROM public.{dbcfg.ANALYSIS_REPORTS_TABLE_NAME}
            WHERE ticker = :ticker
            ORDER BY backtest_date DESC
        """
        )
        result = self.db.execute(stmt, {"ticker": ticker})
        return result.mappings().all()
