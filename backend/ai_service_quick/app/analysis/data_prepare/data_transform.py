from typing import Any, Dict, List

import pandas as pd
from itapia_common.logger import ITAPIALogger

logger = ITAPIALogger("Data Transformation")


def transform_single_ticker_response(json_res: Dict[str, Any]) -> pd.DataFrame:
    """
    Convert the JSON Response for a single ticker into pandas's DataFrame with DateTimeIndex

    Args:
        json_res (Dict[str, Any]): Response JSON, required `metadata` and `data_points` fields.

    Returns:
        pd.DataFrame: OHLCV DataFrame with DatetimeIndex.

    Raises:
        KeyError: If any required fields is missed
    """
    # Validate and extract data
    logger.info("Transforming single ticker repsonse ...")
    metadata = json_res.get("metadata")
    if not metadata:
        raise KeyError("Response is missing 'metadata' key.")

    data_points = json_res.get("datas")
    if not data_points:
        logger.warn(
            f"Empty data points for ticker {metadata.get('ticker')}. Returning empty DataFrame."
        )
        return pd.DataFrame()

    # Change list of dicts into DataFrame
    df = pd.DataFrame(data_points)

    # Check required cols
    required_cols = ["timestamp", "open", "high", "low", "close", "volume"]
    if not all(col in df.columns for col in required_cols):
        raise KeyError(
            f"Data points are missing required keys. Expected: {required_cols}"
        )

    # Processing Time index
    df["datetime_utc"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
    df.set_index("datetime_utc", inplace=True)
    df.drop(columns=["timestamp"], inplace=True)
    df.sort_index(inplace=True)

    return df


def transform_multi_ticker_responses(json_list: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert a list of JSON responses (one for each ticker) into a single, concatenated DataFrame.

    Args:
        json_list (List[Dict[str, Any]]): List of JSON Response, each required `metadata`
            and `data_points` fields. If a JSON Response missing one of these fields, that JSON will be
            skipped.
    Returns:
        pd.DataFrame: A big, concated DataFrame contains datas of all tickers.
    """
    all_dfs = []

    logger.info(f"Transforming data for {len(json_list)} tickers...")

    for json_res in json_list:
        try:
            metadata = json_res.get("metadata")
            if not metadata or not metadata.get("ticker"):
                logger.warn(
                    "Found a response with missing metadata or ticker. Skipping."
                )
                continue

            single_df = transform_single_ticker_response(json_res)

            if not single_df.empty:
                # Add a `ticker` columns to distinguish data.
                single_df["ticker"] = metadata["ticker"]
                all_dfs.append(single_df)

        except KeyError as e:
            logger.err(f"Could not process a response. Error: {e}. Skipping.")
            continue

    if not all_dfs:
        logger.warn("No valid data found to concatenate.")
        return pd.DataFrame()

    # Concat all dfs
    final_df = pd.concat(all_dfs)

    return final_df
