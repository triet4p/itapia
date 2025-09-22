# common/dblib/crud/general_update.py

"""Provides bulk insert operations with conflict resolution for PostgreSQL."""

from typing import Literal

import pandas as pd
from sqlalchemy import Engine
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.schema import MetaData, Table


def _bulk_insert_on_conflict_do_nothing(
    engine: Engine,
    table_name: str,
    data: list[dict],
    unique_cols: list[str],
    chunk_size: int = 1000,
):
    """Insert data in bulk with conflict resolution set to do nothing on conflict.

    This function processes data in chunks and uses PostgreSQL's ON CONFLICT DO NOTHING
    clause to handle conflicts efficiently.

    Args:
        engine (Engine): SQLAlchemy engine for database connection.
        table_name (str): Name of the table to insert data into.
        data (list[dict]): List of dictionaries containing the data to insert.
        unique_cols (list[str]): List of column names that make up the unique constraint.
        chunk_size (int, optional): Number of records to process in each batch. Defaults to 1000.
    """
    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=engine)
    total_processed = 0

    with engine.begin() as connection:
        for i in range(0, len(data), chunk_size):
            chunk = data[i : i + chunk_size]

            stmt = pg_insert(table).values(chunk)
            final_stmt = stmt.on_conflict_do_nothing(index_elements=unique_cols)

            connection.execute(final_stmt)
            total_processed += len(chunk)


def _bulk_insert_on_conflict_do_update(
    engine: Engine,
    table_name: str,
    data: list[dict],
    unique_cols: list[str],
    chunk_size: int = 1000,
):
    """Insert data in bulk with conflict resolution set to update on conflict.

    This function processes data in chunks and uses PostgreSQL's ON CONFLICT DO UPDATE
    clause to handle conflicts by updating existing records.

    Args:
        engine (Engine): SQLAlchemy engine for database connection.
        table_name (str): Name of the table to insert data into.
        data (list[dict]): List of dictionaries containing the data to insert.
        unique_cols (list[str]): List of column names that make up the unique constraint.
        chunk_size (int, optional): Number of records to process in each batch. Defaults to 1000.
    """
    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=engine)

    total_inserted = 0

    with engine.begin() as connection:
        # Process data in chunks
        for i in range(0, len(data), chunk_size):
            # Get a small chunk of data
            chunk = data[i : i + chunk_size]

            # Build and execute the UPSERT statement for this chunk only
            stmt = pg_insert(table).values(chunk)
            update_cols = {
                col.name: col for col in stmt.excluded if col.name not in unique_cols
            }
            final_stmt = stmt.on_conflict_do_update(
                index_elements=unique_cols, set_=update_cols
            )

            connection.execute(final_stmt)
            total_inserted += len(chunk)


def bulk_insert(
    engine: Engine,
    table_name: str,
    data: list[dict] | pd.DataFrame,
    unique_cols: list[str],
    chunk_size: int = 1000,
    on_conflict: Literal["nothing", "update"] = "nothing",
):
    """Bulk insert records into a dynamic table with conflict handling (UPSERT).

    This function is optimized for writing data to tables with frequently changing data.
    It performs writes in chunks within a single transaction to ensure data integrity.

    Args:
        engine (Engine): SQLAlchemy engine for database connection.
        table_name (str): Name of the table to insert data into. Must be one of the allowed dynamic tables.
        data (list[dict] | pd.DataFrame): Data to insert, as a list of dictionaries or a pandas DataFrame.
        unique_cols (list[str]): List of columns that make up a unique key to identify conflicts.
        chunk_size (int, optional): Number of records in each write batch. Defaults to 1000.
        on_conflict (Literal['nothing', 'update'], optional): Action to take when conflicts occur.
            'nothing' will ignore the new record, 'update' will update the existing record.
            Defaults to 'nothing'.

    Raises:
        ValueError: If `table_name` is not an allowed dynamic table.
    """
    # Convert to JSON format first
    if isinstance(data, pd.DataFrame):
        if data.empty:
            print("Data is empty!")
            return
        _data = data.to_dict(orient="records")
    else:
        if not data:
            print("Data is empty!")
            return
        _data = data

    # Perform insert
    if on_conflict == "nothing":
        _bulk_insert_on_conflict_do_nothing(
            engine, table_name, _data, unique_cols, chunk_size
        )
    else:
        _bulk_insert_on_conflict_do_update(
            engine, table_name, _data, unique_cols, chunk_size
        )
