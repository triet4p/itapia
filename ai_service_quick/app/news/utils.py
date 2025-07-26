from pathlib import Path
import pandas as pd
from typing import List, Set
import re

def load_dictionary(filepath: str) -> Set[str]:
    """Đọc một file CSV từ điển và trả về một set các từ đã được chuẩn hóa."""
    file_path = Path(filepath)
    if not file_path.exists():
        raise FileNotFoundError(f"Dictionary file not found at: {file_path}")
    
    df = pd.read_csv(file_path, header=None)
    return set(df.iloc[:, 0].str.lower())

def preprocess_news_texts(texts: List[str]) -> List[str]:
    """
    Dọn dẹp danh sách các văn bản tin tức trước khi đưa vào phân tích.
    - Chuyển về chữ thường.
    - Loại bỏ mã ticker trong dấu ngoặc đơn.
    """
    cleaned_texts = []
    # Biểu thức chính quy tìm một khoảng trắng (tùy chọn), dấu ngoặc đơn mở,
    # các ký tự chữ và số bên trong, và một dấu ngoặc đơn đóng.
    ticker_pattern = re.compile(r'\s*\([A-Z0-9\.]+\)')
    
    for text in texts:
        # 1. Loại bỏ mã ticker
        no_tickers_text = ticker_pattern.sub('', text)
        # 2. Chuyển về chữ thường
        lower_text = no_tickers_text.lower()
        cleaned_texts.append(lower_text)
        
    return cleaned_texts