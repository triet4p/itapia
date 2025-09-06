"""Data splitting utilities for forecasting model training."""

from typing import Generator, Tuple
import pandas as pd
from datetime import datetime


def train_test_split(df: pd.DataFrame,
                     train_test_split_date: datetime,
                     test_last_date: datetime) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split DataFrame into train and test sets based on date thresholds.
    
    Args:
        df (pd.DataFrame): Input DataFrame to split
        train_test_split_date (datetime): Date to split train and test sets
        test_last_date (datetime): Last date for test set
        
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: Tuple of (train_df, test_df)
    """
    _train_test_split_date = pd.to_datetime(train_test_split_date, utc=True)
    _test_last_date = pd.to_datetime(test_last_date, utc=True)
    
    df_train = df[df.index <= _train_test_split_date]
    df_test = df[(df.index > _train_test_split_date) & (df.index <= _test_last_date)]
    
    return df_train, df_test


def get_walk_forward_splits(
    df: pd.DataFrame, 
    validation_months: int = 3,
    min_train_months: int = 6,
    max_train_months: int = None
) -> Generator[Tuple[pd.DataFrame, pd.DataFrame], None, None]:
    """Generate (train, validation) pairs for Walk-Forward Validation by year,
    with customizable validation set size.
    
    This function divides data into yearly blocks. In each year, the last months
    (defined by `validation_months`) are used as the validation set, and the rest
    of that year plus all previous years are used as the training set.
    
    Args:
        df (pd.DataFrame): Input DataFrame with DatetimeIndex
        validation_months (int, optional): Number of months at the end of each year to use
            as validation set. Defaults to 3 (i.e., Q4)
        min_train_months (int, optional): Minimum number of months in a year to be considered
            a valid "block" for splitting. Helps skip years with too little data. Defaults to 6
        max_train_months (int, optional): Maximum number of months to include in training set.
            If None, uses expanding window. If specified, uses sliding window
            
    Yields:
        Generator[Tuple[pd.DataFrame, pd.DataFrame], None, None]: 
            A generator that yields pairs of (train_df, valid_df)
            
    Raises:
        TypeError: If DataFrame index is not a DatetimeIndex
        ValueError: If validation_months is not between 1 and 11, or if max_train_months is not positive
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("DataFrame index must be a DatetimeIndex.")
    if not 1 <= validation_months <= 11:
        raise ValueError("validation_months must be between 1 and 11.")
    if max_train_months is not None and max_train_months <= 0:
        raise ValueError("max_train_months must be a positive integer.")

    # Sort to ensure chronological order
    df = df.sort_index()
    
    start_year = df.index.min().year
    end_year = df.index.max().year

    print(f"Generating splits from {start_year} to {end_year} with {validation_months}-month validation...")
    if max_train_months:
        print(f"  - Mode: Sliding Window (max train size: {max_train_months} months)")
    else:
        print("  - Mode: Expanding Window (full history)")

    for year in range(start_year, end_year + 1):
        year_data = df[df.index.year == year]

        # Check if current year has enough data
        if year_data.index.month.nunique() < min_train_months:
            print(f"  - Skipping year {year}: not enough data.")
            continue

        # Determine start month of validation set
        # Example: if validation_months=3, val_start_month will be 10 (October)
        val_start_month = 12 - validation_months + 1
        
        valid_df = year_data[year_data.index.month >= val_start_month]

        # Handle case where last year might not have enough validation months
        if valid_df.empty:
            print(f"  - Skipping validation for year {year}: no data in the last {validation_months} months.")
            continue
            
        validation_start_date = valid_df.index.min()
        if max_train_months is not None:
            # Sliding Window mode
            train_start_date = validation_start_date - pd.DateOffset(months=max_train_months)
            train_df = df[(df.index >= train_start_date) & (df.index < validation_start_date)]
        else:
            # Expanding Window mode (as before)
            train_df = df[df.index < validation_start_date]


        if not train_df.empty:
            print(f"  - Yielding Split for year {year}:")
            print(f"    - Train: {train_df.index.min().date()} -> {train_df.index.max().date()} (shape: {train_df.shape})")
            print(f"    - Valid: {valid_df.index.min().date()} -> {valid_df.index.max().date()} (shape: {valid_df.shape})")
            yield train_df, valid_df