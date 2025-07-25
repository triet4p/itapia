FROM continuumio/miniconda3

# Đặt thư mục làm việc
WORKDIR /ai-service-quick

# --- BƯỚC 1: TẠO MÔI TRƯỜNG CONDA MỚI VỚI PHIÊN BẢN PYTHON CỤ THỂ ---
# Đây là cách làm tốt nhất để kiểm soát phiên bản.
# Chúng ta tạo một môi trường tên là 'itapia' với Python 3.11
RUN conda create -n itapia python=3.11 -y

# --- BƯỚC 2: KÍCH HOẠT MÔI TRƯỜNG MỚI VÀ CÀI ĐẶT THƯ VIỆN ---
# Sử dụng 'conda run' để thực thi các lệnh bên trong môi trường 'itapia'
# 2.1. Cài đặt TA-Lib trước tiên
RUN conda run -n itapia conda install -c conda-forge -y ta-lib

# 2.2. Cài đặt các gói còn lại bằng pip
COPY ./ai_service_quick/requirements.txt /ai-service-quick/requirements.txt
RUN conda run -n itapia pip install --no-cache-dir --upgrade -r /ai-service-quick/requirements.txt

COPY ./shared /tmp/shared-itapia
RUN conda run -n itapia pip install -e /tmp/shared-itapia

COPY ./ai_service_quick /ai-service-quick

RUN chmod +x /ai-service-quick/entrypoint.sh

RUN ls /ai-service-quick -l