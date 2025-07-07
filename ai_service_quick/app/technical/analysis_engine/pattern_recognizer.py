import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from typing import List, Dict, Callable, Optional

# --- DECORATOR VÀ SỔ ĐĂNG KÝ ---
# Sổ đăng ký sẽ là một dictionary, lưu tên mẫu hình và hàm kiểm tra tương ứng
# Nó được định nghĩa ở cấp độ module
_chart_pattern_registry: Dict[str, Callable[..., Optional[Dict]]] = {}

def register_pattern(pattern_name: str):
    def decorator(func):
        # Đăng ký hàm 'func' với tên 'pattern_name'
        _chart_pattern_registry[pattern_name] = func
        # Trả về hàm gốc mà không thay đổi nó
        return func
    return decorator

class PatternRecognizer:
    CHART_PATTERN_METADATA = {
        "Double Top": {"sentiment": "Bearish"},
        "Double Bottom": {"sentiment": "Bullish"},
        "Head and Shoulders": {"sentiment": "Bearish"}
        # ...
    }
    def __init__(self, featured_df: pd.DataFrame, 
                 history_window: int = 90,
                 prominence_pct: float = 0.015, 
                 distance: int = 5):
        if featured_df.empty or len(featured_df) < history_window:
            raise ValueError(f"Input DataFrame must have at least {history_window} rows.")
        
        self.df = featured_df
        self.analysis_df = self.df.tail(history_window).copy()
        self.latest_row = self.analysis_df.iloc[-1]
        
        self.peaks, self.troughs = self._find_extrema(prominence_pct, distance) 
        
    def find_patterns(self) -> List[Dict]:
        print("--- PatternRecognizer: Finding Patterns (Extensible) ---")
        all_patterns = []
        all_patterns.extend(self._find_candlestick_patterns())
        all_patterns.extend(self._find_chart_patterns())
        return all_patterns
        
    def _find_extrema(self, prominence_pct: float, distance: int):
        avg_price = np.mean(self.analysis_df['high'])
        required_prominence = avg_price * prominence_pct
        
        peaks_indices, _ = find_peaks(self.analysis_df['high'], 
                                      prominence=required_prominence,
                                      distance=distance)
        
        troughs_indices, _ = find_peaks(-self.analysis_df['low'], 
                                        prominence=required_prominence, 
                                        distance=distance)
        
        peaks_df = pd.DataFrame({'index_in_df': self.analysis_df.index[peaks_indices], 
                                 'price': self.analysis_df['high'].iloc[peaks_indices].values})
        troughs_df = pd.DataFrame({'index_in_df': self.analysis_df.index[troughs_indices], 
                                   'price': self.analysis_df['low'].iloc[troughs_indices].values})
        
        return peaks_df, troughs_df 

    def _find_candlestick_patterns(self) -> List[Dict]:
        patterns = []
        latest_row_lower = self.latest_row.rename(index=str.lower)
        for col, value in latest_row_lower.items():
            col = str(col)
            if col.startswith('cdl_') and value != 0:
                pattern_name = col.replace('cdl_', '').replace('_', ' ').title()
                sentiment = "Bullish" if value > 0 else "Bearish"
                
                result = {
                    "pattern_name": pattern_name,
                    "type": "Candlestick Pattern",
                    "sentiment": sentiment,
                    "evidence": {
                        "date": str(self.latest_row.name)
                    }
                }
                patterns.append(result)
        return patterns
    
    def _find_chart_patterns(self) -> List[Dict]:
        found_patterns = []
        for pattern_name, checker_function in _chart_pattern_registry.items():
            evidence = checker_function(self)
            if evidence is not None:
                metadata = self.get_pattern_metadata(pattern_name)
                res = {
                    "pattern_name": pattern_name,
                    "type": "Chart Pattern",
                    "sentiment": metadata.get("sentiment", "Neutral"),
                    "evidence": evidence
                }
                found_patterns.append(res)

        return found_patterns
    
    def get_pattern_metadata(self, pattern_name: str) -> Dict:
        return PatternRecognizer.CHART_PATTERN_METADATA.get(pattern_name, {})
    
    # --- ĐĂNG KÝ CÁC HÀM KIỂM TRA MẪU HÌNH ---

    @register_pattern("Double Top")
    def _is_double_top(self, tolerance: float = 0.015) -> Optional[Dict]:
        if len(self.peaks) < 2 or len(self.troughs) < 1: 
            return None
        p2, p1 = self.peaks.iloc[-1], self.peaks.iloc[-2]
        troughs_between = self.troughs[(self.troughs['index_in_df'] > p1.index_in_df) & (self.troughs['index_in_df'] < p2.index_in_df)]
        if troughs_between.empty: 
            return None
        neckline = troughs_between.iloc[-1]
        height_similarity = abs(p1.price - p2.price) / ((p1.price + p2.price) / 2) < tolerance
        is_confirmed = self.latest_row['close'] < neckline.price
        
        all_conditions = p1.price > neckline.price and p2.price > neckline.price and height_similarity and is_confirmed
        if all_conditions:
            evidence = {
                "peak1_date": str(p1.index_in_df),
                "peak1_price": p1.price,
                "peak2_date": str(p2.index_in_df),
                "peak2_price": p2.price,
                "neckline_date": str(neckline.index_in_df),
                "neckline_price": neckline.price,
                "confirmation_date": str(self.latest_row.name),
                "params": {
                    "tolerance": tolerance
                }
            }
        else:
            evidence = None
        
        return evidence

    @register_pattern("Double Bottom")
    def _is_double_bottom(self, tolerance: float = 0.015) -> Optional[Dict]:
        if len(self.troughs) < 2 or len(self.peaks) < 1: 
            return None
        t2, t1 = self.troughs.iloc[-1], self.troughs.iloc[-2]
        peaks_between = self.peaks[(self.peaks['index_in_df'] > t1.index_in_df) & (self.peaks['index_in_df'] < t2.index_in_df)]
        if peaks_between.empty: 
            return None
        neckline = peaks_between.iloc[-1]
        depth_similarity = abs(t1.price - t2.price) / ((t1.price + t2.price) / 2) < tolerance
        is_confirmed = self.latest_row['close'] > neckline.price
        
        all_conditions = t1.price < neckline.price and t2.price < neckline.price and depth_similarity and is_confirmed
        if all_conditions:
            evidence = {
                "trough1_date": str(t1.index_in_df),
                "trough1_price": t1.price,
                "trough2_date": str(t2.index_in_df),
                "trough2_price": t2.price,
                "neckline_date": str(neckline.index_in_df),
                "neckline_price": neckline.price,
                "confirmation_date": str(self.latest_row.name),
                "params": {
                    "tolerance": tolerance
                }
            }
        else:
            evidence = None
        
        return evidence

    @register_pattern("Head and Shoulders")
    def _is_head_and_shoulders(self, tolerance: float = 0.015) -> Optional[Dict]:
        if len(self.peaks) < 3 or len(self.troughs) < 2: 
            return None
        p3, p2, p1 = self.peaks.iloc[-1], self.peaks.iloc[-2], self.peaks.iloc[-3]
        troughs_after_p1 = self.troughs[self.troughs['index_in_df'] > p1.index_in_df]
        if len(troughs_after_p1) < 2: 
            return None
        t1, t2 = troughs_after_p1.iloc[0], troughs_after_p1.iloc[1]
        is_structured = (p1.index_in_df < t1.index_in_df < p2.index_in_df < t2.index_in_df < p3.index_in_df)
        if not is_structured: 
            return None
        head_is_highest = p2.price > p1.price and p2.price > p3.price
        shoulders_are_similar = abs(p1.price - p3.price) / ((p1.price + p3.price) / 2) < tolerance
        neckline_level = min(t1.price, t2.price)
        is_confirmed = self.latest_row['close'] < neckline_level
        
        all_conditions = head_is_highest and shoulders_are_similar and is_confirmed
        
        if all_conditions:
            evidence = {
                "peak1_date": str(p1.index_in_df),
                "peak1_price": p1.price,
                "peak2_date": str(p2.index_in_df),
                "peak2_price": p2.price,
                "peak3_date": str(p3.index_in_df),
                "peak3_price": p3.price,
                "trough1_date": str(t1.index_in_df),
                "trough1_price": t1.price,
                "trough2_date": str(t2.index_in_df),
                "trough2_price": t2.price,
                "neckline_level": neckline_level,
                "confirmation_date": str(self.latest_row.name),
                "params": {
                    "tolerance": tolerance
                }
            }
        else:
            evidence = None
        
        return evidence