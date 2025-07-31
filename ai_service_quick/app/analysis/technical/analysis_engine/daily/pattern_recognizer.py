import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from typing import List, Dict, Callable, Literal, Optional

from itapia_common.schemas.entities.analysis.technical.daily import PatternObj, PatternReport

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

class DailyPatternRecognizer:
    CHART_PATTERN_METADATA = {
        "Double Top": {"sentiment": "bear", "score": 100},
        "Double Bottom": {"sentiment": "bull", "score": 100},
        "Head and Shoulders": {"sentiment": "bear", "score": 100}
        # ...
    }
    
    CDL_NAME_MAPPING = {
        'cdl_2crows': 'Two Crows',
        'cdl_3blackcrows': 'Three Black Crows',
        'cdl_3inside': 'Three Inside Up/Down',
        'cdl_3linestrike': 'Three-Line Strike',
        'cdl_3outside': 'Three Outside Up/Down',
        'cdl_3starsinsouth': 'Three Stars In The South',
        'cdl_3whitesoldiers': 'Three White Soldiers',
        'cdl_abandonedbaby': 'Abandoned Baby',
        'cdl_engulfing': 'Engulfing', # Đây là mẫu hình quan trọng
        'cdl_eveningdojistar': 'Evening Doji Star',
        'cdl_eveningstar': 'Evening Star',
        'cdl_hammer': 'Hammer',
        'cdl_hangingman': 'Hanging Man',
        'cdl_harami': 'Harami',
        'cdl_haramicross': 'Harami Cross',
        'cdl_invertedhammer': 'Inverted Hammer',
        'cdl_morningdojistar': 'Morning Doji Star',
        'cdl_morningstar': 'Morning Star',
        'cdl_piercing': 'Piercing Pattern',
        'cdl_shootingstar': 'Shooting Star',
        'cdl_doji': 'Doji', # Doji chung, nên có điểm thấp
        'cdl_dragonflydoji': 'Dragonfly Doji',
        'cdl_gravestonedoji': 'Gravestone Doji',
        'cdl_longleggeddoji': 'Long-Legged Doji',
    }
    
    CANDLESTICK_METADATA = {
        # Mẫu hình đảo chiều mạnh (3 nến)
        "Three Black Crows": {"sentiment": "bear", "score": 85},
        "Three White Soldiers": {"sentiment": "bull", "score": 85},
        "Morning Star": {"sentiment": "bull", "score": 80},
        "Evening Star": {"sentiment": "bear", "score": 80},
        "Abandoned Baby": {"sentiment": "bull", "score": 90}, # Rất hiếm nhưng mạnh
        
        # Mẫu hình nhấn chìm (2 nến)
        "Engulfing": {"sentiment": "varies", "score": 75}, # Sentiment phụ thuộc vào giá trị
        "Harami": {"sentiment": "varies", "score": 70},
        "Piercing Pattern": {"sentiment": "bull", "score": 70},

        # Mẫu hình đơn lẻ
        "Hammer": {"sentiment": "bull", "score": 60},
        "Hanging Man": {"sentiment": "bear", "score": 60},
        "Inverted Hammer": {"sentiment": "bull", "score": 60},
        "Shooting Star": {"sentiment": "bear", "score": 60},
        
        # Doji (do dự)
        "Doji": {"sentiment": "neutral", "score": 30},
        "Dragonfly Doji": {"sentiment": "bull", "score": 40},
        "Gravestone Doji": {"sentiment": "bear", "score": 40},
        "Long-Legged Doji": {"sentiment": "neutral", "score": 35},
    }
    
    def __init__(self, featured_df: pd.DataFrame, 
                 history_window: int = 90,
                 prominence_pct: float = 0.015, 
                 distance: int = 5,
                 lookback_period: int = 5,
                 top_patterns: int = 4):
        if featured_df.empty or len(featured_df) < history_window:
            raise ValueError(f"Input DataFrame must have at least {history_window} rows.")
        
        self.df = featured_df
        self.analysis_df = self.df.tail(history_window).copy()
        self.latest_row = self.analysis_df.iloc[-1]
        
        self.lookback_period = lookback_period
        self.history_window = history_window
        self.prominence_pct = prominence_pct
        self.distance = distance
        self.top_patterns = top_patterns
        
        self.peaks, self.troughs = self._find_extrema(prominence_pct, distance) 
        
    def find_patterns(self):
        all_patterns = []
        all_patterns.extend(self._find_candlestick_patterns(self.lookback_period))
        all_patterns.extend(self._find_chart_patterns())
        
        finals = self._filter_and_prioritize(all_patterns)
        return PatternReport(
            history_window=self.history_window,
            prominence_pct=self.prominence_pct,
            distance=self.distance,
            lookback_period=self.lookback_period,
            num_top_patterns=self.top_patterns,
            top_patterns=finals[:self.top_patterns]
        )
        
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

    def _find_candlestick_patterns(self, lookback_period: int):
        """
        Quét N ngày cuối cùng và thu thập tất cả các mẫu hình nến bằng
        cách sử dụng bảng ánh xạ tên.
        """
        collected: List[PatternObj] = []
        recent_df = self.analysis_df.tail(lookback_period)
        
        for date, row in recent_df.iterrows():
            row_lower_cols = row.rename(index=str.lower)
            
            for cdl_col_name, friendly_name in self.CDL_NAME_MAPPING.items():
                # Kiểm tra xem cột có tồn tại và có giá trị không
                if cdl_col_name in row_lower_cols and row_lower_cols[cdl_col_name] != 0:
                    
                    metadata = self.CANDLESTICK_METADATA.get(friendly_name, {})
                    
                    # Xác định sentiment dựa trên giá trị (100 là bull, -100 là bear)
                    sentiment = "bull" if row_lower_cols[cdl_col_name] > 0 else "bear"
                    
                    # Ghi đè sentiment nếu metadata có định nghĩa khác (ví dụ: neutral)
                    if metadata.get("sentiment") != "varies":
                        sentiment = metadata.get("sentiment", "neutral")

                    collected.append(PatternObj(
                        name=friendly_name,
                        pattern_type='candlestick',
                        sentiment=sentiment,
                        score=metadata.get('score', 20),
                        confirmation_date=date.date().isoformat(),
                        evidence={}
                    ))
        
        return collected
    
    def _find_chart_patterns(self) -> List[PatternObj]:
        found_patterns: List[PatternObj] = []
        for pattern_name, checker_function in _chart_pattern_registry.items():
            evidence = checker_function(self)
            if evidence is not None:
                metadata = self.get_pattern_metadata(pattern_name, 'chart')
                res = PatternObj(
                    name=pattern_name,
                    pattern_type='chart',
                    sentiment=metadata.get("sentiment", "neutral"),
                    score=metadata.get("score", 30),
                    confirmation_date=self.latest_row.name.date().isoformat(),
                    evidence=evidence
                )
                found_patterns.append(res)

        return found_patterns
    
    def _filter_and_prioritize(self, patterns: List[PatternObj]) -> List[PatternObj]:
        """
        Lọc bỏ các mẫu hình nhiễu và sắp xếp theo mức độ quan trọng.
        """
        if not patterns:
            return []
        patterns_as_dicts = [p.model_dump() for p in patterns]

        # 1. Loại bỏ các mẫu hình chung chung nếu có mẫu hình cụ thể hơn trong cùng một ngày
        df = pd.DataFrame(patterns_as_dicts)
        
        # Ví dụ: Nếu ngày X có cả 'Doji' và 'Dragonfly Doji', chúng ta muốn bỏ 'Doji'
        # Tạo một cột để xác định ngày của bằng chứng
        df['confirmation_date_dt'] = pd.to_datetime(df['confirmation_date'])
        
        # Danh sách các mẫu hình chung chung cần loại bỏ nếu có "con" của nó
        generic_patterns = {"Doji"}
        specific_patterns = {"Dragonfly Doji", "Gravestone Doji"}
        
        indices_to_drop = []
        for date, group in df.groupby('confirmation_date_dt'):
            names_in_group = set(group['name'])
            if names_in_group.intersection(generic_patterns) and names_in_group.intersection(specific_patterns):
                # Tìm index của các mẫu hình chung chung trong ngày này để xóa
                indices = group[group['name'].isin(generic_patterns)].index
                indices_to_drop.extend(indices)
                
        df.drop(indices_to_drop, inplace=True)
        
        # 2. Sắp xếp kết quả cuối cùng
        # Ưu tiên 1: Điểm số (Score) cao hơn
        # Ưu tiên 2: Ngày gần đây hơn
        df = df.sort_values(by=['score', 'confirmation_date_dt'], ascending=[False, False])
        #df['confirmation_date'] = df['confirmation_date'].dt.isoformat()
        
        # Chuyển lại thành list of dicts
        records = df.to_dict('records')
        return [PatternObj.model_validate(record) for record in records]
    
    def get_pattern_metadata(self, pattern_name: str,
                             pattern_type: Literal['chart', 'candlestick']) -> Dict:
        if pattern_type == 'chart':
            return DailyPatternRecognizer.CHART_PATTERN_METADATA.get(pattern_name, {})
        elif pattern_type == 'candlestick':
            return DailyPatternRecognizer.CANDLESTICK_METADATA.get(pattern_name, {})
        return {}
    
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
                "peak1_date": p1.index_in_df.date().isoformat(),
                "peak1_price": p1.price,
                "peak2_date": p2.index_in_df.date().isoformat(),
                "peak2_price": p2.price,
                "neckline_date": neckline.index_in_df.date().isoformat(),
                "neckline_price": neckline.price,
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
                "trough1_date": t1.index_in_df.date().isoformat(),
                "trough1_price": t1.price,
                "trough2_date": t2.index_in_df.date().isoformat(),
                "trough2_price": t2.price,
                "neckline_date": neckline.index_in_df.date().isoformat(),
                "neckline_price": neckline.price,
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
                "peak1_date": p1.index_in_df.date().isoformat(),
                "peak1_price": p1.price,
                "peak2_date": p2.index_in_df.date().isoformat(),
                "peak2_price": p2.price,
                "peak3_date": p3.index_in_df.date().isoformat(),
                "peak3_price": p3.price,
                "trough1_date": t1.index_in_df.date().isoformat(),
                "trough1_price": t1.price,
                "trough2_date": t2.index_in_df.date().isoformat(),
                "trough2_price": t2.price,
                "neckline_level": neckline_level,
                "params": {
                    "tolerance": tolerance
                }
            }
        else:
            evidence = None
        
        return evidence