from typing import List

# Define the order in which tables should be inserted
# This is important due to foreign key constraints
TABLES_INSERT_ORDER: List[str] = [
    'exchanges',
    'sectors',
    'tickers',
    'rules',
]