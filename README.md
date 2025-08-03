
---

# **ITAPIA - Trợ lý Đầu tư Cá nhân Thông minh và Minh bạch dựa trên AI**

ITAPIA (Intelligent and Transparent AI-Powered Personal Investment Assistant) là một dự án đồ án tốt nghiệp với mục tiêu xây dựng một nền tảng hỗ trợ đầu tư chứng khoán thông minh, được thiết kế đặc biệt cho các nhà đầu tư cá nhân.

Khác với các công cụ "hộp đen" truyền thống, ITAPIA tập trung vào **Khả năng Giải thích (Explainability - XAI)**, cung cấp các khuyến nghị minh bạch, và có một tầm nhìn dài hạn về khả năng **học hỏi và đồng tiến hóa** cùng người dùng.

**Tài liệu Kiến trúc & Kỹ thuật chi tiết**: **[itapia-mvp-v1.0.md](./doc/public/itapia-mvp-v1.0.md)**

**English version of README**: [README-en.md](./README-en.md)

---

## 🏗️ Kiến trúc Hệ thống

Hệ thống được xây dựng theo kiến trúc microservices, dựa trên một nền tảng `sharedlib` mạnh mẽ và một cấu trúc điều phối (Orchestrator) phân cấp rõ ràng.

-   **API Gateway** (`api_gateway`): Cổng giao tiếp duy nhất (Single Entry Point), xử lý định tuyến và điều phối request đến dịch vụ nội bộ.
-   **AI Service Quick** (`ai_service_quick`): Bộ não của hệ thống, chạy trên hạ tầng CPU. Nó chứa các module AI cốt lõi và chịu trách nhiệm cho toàn bộ quy trình `Quick Check` để tạo ra các báo cáo phân tích và khuyến nghị.
-   **Data Processing** (`data_processing`): Các service độc lập để thu thập và xử lý dữ liệu (ETL) theo lịch trình (batch) và thời gian thực (real-time).
-   **Data Seeds** (`data_seeds`): Một service chạy một lần để khởi tạo CSDL với schema và dữ liệu ban đầu (bao gồm các quy tắc dựng sẵn).
-   **Databases**: PostgreSQL (với `JSONB`) để lưu trữ dữ liệu có cấu trúc, bền vững (giá, tin tức, quy tắc) và Redis để lưu cache và dữ liệu streaming thời gian thực.

### Sơ đồ Triển khai

![Deployment Architecture](doc/diagram/UML-deployment.png)

*Trong phạm vi đồ án, tất cả các thành phần được triển khai bằng Docker và Docker Compose.*

---

## 🚀 Bắt đầu Nhanh (Quick Start)

### Yêu cầu Hệ thống
- **Docker & Docker Compose**
- **Python 3.11+**
- **Git**

### Quy trình Cài đặt & Chạy

**Bước 1: Clone Repository và Cấu hình Môi trường**
```bash
git clone https://github.com/triet4p/itapia.git
cd itapia
# Tạo file .env từ file mẫu và điền thông tin Kaggle của bạn
cp .env.template .env
```

**Bước 2: Build tất cả các Docker Image**
*Lệnh này sẽ build image cho `data-processing`, `data-seeds`, `ai-service-quick`, và `api-gateway`.*
```bash
docker-compose build
```

**Bước 3: Khởi tạo và "Seed" Cơ sở dữ liệu**
*Lệnh này sẽ khởi động CSDL, tạo các bảng, và nạp vào các quy tắc dựng sẵn.*
```bash
# Khởi động CSDL và chờ chúng sẵn sàng
docker-compose up -d stocks_postgre_db realtime_redis_db

# Chờ khoảng 10-15 giây để CSDL khởi động hoàn toàn
sleep 15 

# Chạy service seeding, nó sẽ tự thoát sau khi hoàn thành
docker-compose up data-seeds
```

**Bước 4: Khởi động Toàn bộ Hệ thống**
```bash
# Khởi động các service xử lý dữ liệu nền và các service ứng dụng
docker-compose up -d
```
*Lưu ý: `ai-service-quick` có thể mất vài phút ở lần khởi động đầu tiên để tải về và cache các mô hình AI từ Kaggle/Hugging Face.*

**Bước 5: Truy cập Hệ thống**
- **API Gateway (Tài liệu API Công khai)**: **http://localhost:8000/docs**
- **AI Service Quick (Tài liệu API Nội bộ)**: http://localhost:8001/docs

---

## 🗺️ Danh sách API

Tất cả các tương tác bên ngoài đều thông qua **API Gateway**. Dưới đây là các nhóm endpoint chính.

*(Prefix `/api/v1` được áp dụng cho tất cả)*

### **Advisor - Khuyến nghị & Suy luận (Cấp cao nhất)**
*   `GET /advisor/quick/{ticker}`: Lấy báo cáo khuyến nghị **đầy đủ** (JSON). **Đây là endpoint chính.**
*   `GET /advisor/quick/{ticker}/explain`: Lấy bản giải thích bằng **ngôn ngữ tự nhiên** cho báo cáo khuyến nghị.

### **Analysis - Dữ liệu Phân tích Chi tiết**
*   `GET /analysis/quick/{ticker}`: Lấy báo cáo phân tích tổng hợp (Technical, Forecasting, News).
*   `GET /analysis/quick/{ticker}/technical`: Chỉ lấy báo cáo Phân tích Kỹ thuật.
*   `GET /analysis/quick/{ticker}/forecasting`: Chỉ lấy báo cáo Dự báo.
*   `GET /analysis/quick/{ticker}/news`: Chỉ lấy báo cáo Phân tích Tin tức.

### **Rules - Quản lý & Giải thích Quy tắc**
*   `GET /rules`: Lấy danh sách tóm tắt tất cả các quy tắc dựng sẵn.
*   `GET /rules/{rule_id}`: Lấy chi tiết cấu trúc (cây logic JSON) của một quy tắc.
*   `GET /rules/{rule_id}/explain`: Lấy bản giải thích logic của một quy tắc bằng ngôn ngữ tự nhiên.

### **Market Data - Dữ liệu Thị trường Thô**
*   `GET /market/tickers/{ticker}/prices/daily`: Lấy dữ liệu giá lịch sử hàng ngày.
*   `GET /market/tickers/{ticker}/prices/intraday?latest_only=True/False`: Lấy điểm dữ liệu giá mới nhất trong ngày.
*   `GET /market/tickers/{ticker}/news`: Lấy các tin tức liên quan đến một cổ phiếu.
*   ... và các endpoint dữ liệu khác.

### **Metadata - Dữ liệu Nền**
*   `GET /metadata/sectors`: Lấy danh sách tất cả các nhóm ngành được hỗ trợ.

---

## 📈 Quy trình Huấn luyện Mô hình

Do giới hạn tài nguyên, các quy trình huấn luyện được thực hiện trên Kaggle/Colab.
`ai-service-quick` có một cơ chế để xuất dữ liệu đã được làm giàu, sẵn sàng cho việc huấn luyện.

**Cách xuất dữ liệu cho ngành 'TECH':**
```bash
docker-compose exec ai-service-quick conda run -n itapia python -m app.analysis.orchestrator TECH
```
*File CSV sẽ được lưu trong thư mục `ai_service_quick/local/`.*

Chi tiết về quy trình huấn luyện có thể xem tại [Local Training Notebook](./notebooks/itapia-training.ipynb).

---

## 🔧 Cấu trúc Dự án
```
itapia/
├── api_gateway/        # Dịch vụ API Gateway (FastAPI)
├── ai_service_quick/   # Dịch vụ AI cho Quick Check (FastAPI, CPU)
├── data_processing/    # Các pipeline thu thập dữ liệu (ETL)
├── data_seeds/         # Các script khởi tạo CSDL
├── doc/                # Tài liệu chi tiết của dự án
├── shared/             # Thư viện chung (shared library)
├── docker-compose.yml  # Cấu hình các dịch vụ Docker
└── README.md
```

---

## 📈 Các Tính năng Chính (MVP v1.0)

- **AI Giải thích được (XAI)**: Mọi khuyến nghị đều đi kèm với "bằng chứng" là danh sách các quy tắc đã được kích hoạt, cung cấp sự minh bạch tuyệt đối.
- **Kiến trúc Điều phối Phân cấp**: Một kiến trúc backend rõ ràng (`CEO` -> `Phó CEO` -> `Trưởng phòng`), giúp hệ thống dễ bảo trì và mở rộng.
- **Rule Engine Mạnh mẽ**: Một "ngôn ngữ" quy tắc nội bộ dựa trên Cây Biểu thức Tượng trưng và Định kiểu Ngữ nghĩa (STGP), làm nền tảng cho cả các quy tắc chuyên gia và thuật toán tiến hóa trong tương lai.
- **Phân tích Đa luồng**: Kết hợp tín hiệu từ Phân tích Kỹ thuật, Dự báo Machine Learning, và Phân tích Tin tức vào một báo cáo tổng hợp duy nhất.
- **Hệ thống API Toàn diện**: Cung cấp các endpoint từ cấp cao (khuyến nghị) đến cấp thấp (dữ liệu thô), phục vụ cho nhiều mục đích sử dụng.

---

## 🤝 Đóng góp & Trích dẫn
Đây là một dự án đồ án tốt nghiệp. Mọi câu hỏi hoặc gợi ý, xin vui lòng tham khảo **[Tài liệu Kiến trúc & Kỹ thuật chi tiết](./doc/public/itapia-mvp-v1.0.md)**.

### Trích dẫn

Nếu bạn sử dụng công trình này trong nghiên cứu của mình, xin vui lòng trích dẫn:
```txt
[Lê Minh Triết]. (2025). ITAPIA: Trợ lý Đầu tư Cá nhân Thông minh và Minh bạch dựa trên Trí tuệ Nhân tạo. 
Đồ án Tốt nghiệp, Đại học Bách khoa Hà Nội, Việt Nam.
```
**Trích dẫn Mô hình:**
Dự án này sử dụng mô hình phân tích tình cảm tài chính đã được fine-tune, cung cấp bởi Ankit Aglawe.
```bibtex
@misc{AnkitAI_2024_financial_sentiment_model,
  title={DistilBERT Fine-Tuned for Financial Sentiment Analysis},
  author={Ankit Aglawe},
  year={2024},
  howpublished={\url{https://huggingface.co/AnkitAI/distilbert-base-uncased-financial-news-sentiment-analysis}},
}
```
Đối với mục đích thương mại hoặc hợp tác, xin vui lòng liên hệ `trietlm0306@gmail.com`.

---

## 📄 Giấy phép

Dự án này được phát triển như một phần của đồ án tốt nghiệp. Mã nguồn có sẵn cho các mục đích học thuật và giáo dục.