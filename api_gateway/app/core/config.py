# app/core/config.py
"""
Module tập trung hóa việc quản lý và truy cập các biến cấu hình.

Tự động đọc các giá trị từ file `.env` ở thư mục gốc của dự án.
Cung cấp các hằng số đã được định nghĩa cho các thành phần khác trong ứng dụng
sử dụng, đảm bảo tính nhất quán và dễ dàng thay đổi cấu hình từ một nơi duy nhất.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Cấu hình API
GATEWAY_V1_BASE_ROUTE = os.getenv("GATEWAY_V1_BASE_ROUTE", "/api/v1")