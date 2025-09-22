# common/dblib/crud/prices.py
"""Provides CRUD operations for price-related data entities."""

from datetime import datetime, timezone

from redis.client import Redis
from sqlalchemy import Engine, RowMapping, Sequence, text
from sqlalchemy.orm import Session


def get_daily_prices(
    rdbms_session: Session,
    table_name: str,
    ticker: str,
    skip: int = 0,
    limit: int = 500,
) -> Sequence[RowMapping]:

    query = text(
        f"""
        SELECT * FROM public.{table_name} 
        WHERE ticker = :ticker 
        ORDER BY collect_date DESC 
        OFFSET :skip LIMIT :limit
    """
    )

    result = rdbms_session.execute(
        query, {"ticker": ticker, "skip": skip, "limit": limit}
    )
    return result.mappings().all()


def get_tickers_by_sector(
    rdbms_session: Session, table_name: str, sector_code: str
) -> Sequence[str]:

    query = text(
        f"""
        SELECT ticker_sym FROM public.{table_name}
        WHERE sector_code = :sector_code AND is_active = TRUE
        ORDER BY ticker_sym;
    """
    )
    result = rdbms_session.execute(query, {"sector_code": sector_code})
    # .scalars().all() returns a list of values from the first column
    return result.scalars().all()


def get_intraday_prices(
    redis_client: Redis, ticker: str, stream_prefix: str
) -> list[dict] | None:

    if not redis_client:
        return None
    redis_key = f"{stream_prefix}:{ticker}"
    entries = redis_client.xrange(redis_key)
    data_lst = []
    if entries:
        for entry_id, data in entries:
            for key, value in data.items():
                if key in ["open", "high", "low", "close"]:
                    data[key] = float(value)
                elif key == "volume":
                    data[key] = int(value)
                elif key == "last_update_utc":
                    data[key] = datetime.fromisoformat(data[key])
            data["ticker"] = ticker
            data_lst.append(data)
        return data_lst
    else:
        return []


def get_latest_intraday_price(
    redis_client: Redis, ticker: str, stream_prefix: str
) -> dict | None:

    if not redis_client:
        return None
    redis_key = f"{stream_prefix}:{ticker}"
    entries = redis_client.xrevrange(redis_key, count=1)
    if not entries:
        return None
    entry_id, data = entries[0]
    for key, value in data.items():
        if key in ["open", "high", "low", "close"]:
            data[key] = float(value)
        elif key == "volume":
            data[key] = int(value)
        elif key == "last_update_utc":
            data[key] = datetime.fromisoformat(data[key])
    data["ticker"] = ticker

    return data


def get_last_history_date(
    engine: Engine, table_name: str, tickers: list[str], default_return_date: datetime
) -> datetime:

    query = (
        f"SELECT MAX(collect_date) FROM public.{table_name} WHERE ticker IN :tickers;"
    )
    stmt = text(query)

    try:
        with engine.connect() as connection:
            result = connection.execute(stmt, {"tickers": tuple(tickers)}).scalar()
            if result:
                # Convert from DB date to Python datetime
                return datetime.combine(result, datetime.min.time()).replace(
                    tzinfo=timezone.utc
                )
            return default_return_date  # Return default if table is empty
    except Exception:
        # If there's an error (e.g., table doesn't exist), treat as no data
        return default_return_date


def add_intraday_candle(
    redis_client: Redis,
    ticker: str,
    candle_data: dict,
    stream_prefix: str,
    max_entries: int = 300,
):
    """Add an intraday candle to a Redis Stream associated with a ticker.

    Uses Redis Stream data structure to efficiently store time series data.
    The stream will be automatically size-limited to avoid consuming too much memory.

    Args:
        redis_client (Redis): Redis client instance.
        ticker (str): Ticker symbol to identify the stream name (e.g., "intraday_stream:AAPL").
        candle_data (dict): Dictionary containing OHLCV data and other candle information.
        stream_prefix (str): Prefix for the Redis stream key.
        max_entries (int, optional): Maximum number of entries to keep in the stream.
                                   Defaults to 300.
    """
    if not candle_data:
        return
    stream_key = f"{stream_prefix}:{ticker}"

    try:
        # Convert all values to strings for compatibility with Redis Stream
        mapping_to_save = {k: str(v) for k, v in candle_data.items()}

        # XADD command to add a new entry. '*' lets Redis create an ID based on timestamp.
        # MAXLEN ~ max_entries limits the size of the stream.
        redis_client.xadd(
            stream_key, mapping_to_save, maxlen=max_entries, approximate=True
        )

        # No need to set TTL anymore as the stream will automatically trim old data.
        # Data will be automatically replaced the next day.

    except Exception:
        raise
