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
GATEWAY_ALLOW_ORIGINS = os.getenv('GATEWAY_ALLOW_ORIGINS', "").split(",")

# Cấu hình CLient
AI_SERVICE_QUICK_HOST = os.getenv("AI_QUICK_HOST", 'localhost')
AI_SERVICE_QUICK_PORT = os.getenv("AI_QUICK_PORT", 8000)
AI_SERVICE_QUICK_V1_BASE_ROUTE = os.getenv("AI_QUICK_V1_BASE_ROUTE", "/api/v1")
AI_SERVICE_QUICK_BASE_URL = f'http://{AI_SERVICE_QUICK_HOST}:{AI_SERVICE_QUICK_PORT}{AI_SERVICE_QUICK_V1_BASE_ROUTE}'
