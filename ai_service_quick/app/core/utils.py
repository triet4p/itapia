import numpy as np


FORECASTING_TRAINING_BONUS_FEATURES = [
    'open', 'high', 'low', 'close', 'volume',
    'RSI_14', 'ATRr_14', 
    'SMA_50', 'SMA_200',
    'diff_from_sma_50', 'diff_from_sma_200',
    'CDL_ENGULFING', 'CDL_3BLACKCROWS', 'CDL_3WHITESOLDIERS',
    'CDL_MORNINGSTAR', 'CDL_EVENINGSTAR'
]

FORECASTING_TRAINING_SCORE_WEIGHTS = {
    'lgbm': 0.4,
    'rf': 0.3,
    'mi': 0.3
}