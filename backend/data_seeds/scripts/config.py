from typing import List

# Define the order in which tables should be inserted
# This is important due to foreign key constraints
TABLES_INSERT_ORDER: List[str] = [
    'exchanges',
    'sectors',
    'tickers',
    'users',
    'investment_profiles',
    'rules',
    'evo_runs',
    'evo_rules',
    'daily_prices',
    'relevant_news',
    'universal_news',
    'backtest_reports'
]