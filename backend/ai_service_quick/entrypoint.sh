#!/bin/bash
# Dòng trên chỉ định rằng đây là một script shell.

# Dòng này cực kỳ quan trọng. Nó tìm script `conda.sh` và
# "source" nó để các lệnh như `conda activate` có thể hoạt động
# trong script shell này.
source /opt/conda/etc/profile.d/conda.sh

# Kích hoạt môi trường conda mà bạn đã tạo trong Dockerfile
conda activate itapia

# Bây giờ, chạy lệnh uvicorn của bạn.
# Dùng `exec` ở đây sẽ thay thế tiến trình của script shell bằng tiến trình
# của uvicorn, đây là một thực hành tốt.
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload