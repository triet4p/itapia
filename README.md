# ITAPIA - Trợ lý Đầu tư Cá nhân Thông minh và Minh bạch dựa trên AI

ITAPIA (Intelligent and Transparent AI-Powered Personal Investment Assistant) là một dự án đồ án tốt nghiệp với mục tiêu xây dựng một nền tảng hỗ trợ đầu tư chứng khoán thông minh. Dự án được thiết kế đặc biệt cho các nhà đầu tư cá nhân với vốn hạn chế, ưu tiên việc quản lý rủi ro và mong muốn hiểu rõ các khuyến nghị đầu tư do AI đưa ra.

Khác với các công cụ "hộp đen" truyền thống, ITAPIA tập trung vào **khả năng giải thích (Explainability)**, **chi phí thấp**, và khả năng **học hỏi, đồng phát triển** cùng người dùng.

**English version of README**: [README-en.md](./README-en.md)

---

## 🏗️ Kiến trúc Hệ thống

Hệ thống được xây dựng theo kiến trúc microservices, bao gồm các thành phần cốt lõi sau:

-   **API Gateway** (`api_gateway`): Đóng vai trò là cổng giao tiếp duy nhất (Single Entry Point), xử lý xác thực (trong tương lai), định tuyến và điều phối request đến các dịch vụ nội bộ.
-   **AI Service Quick** (`ai_service_quick`): Chạy trên hạ tầng CPU, chịu trách nhiệm cho các quy trình phân tích và dự báo nhanh (Quick Check), trả về kết quả gần như tức thời.
-   **AI Service Deep** (`ai_service_deep` - Tương lai): Chạy trên hạ tầng GPU, dành cho các tác vụ AI/LLM tính toán phức tạp (Deep Dive), hoạt động theo cơ chế bất đồng bộ (asynchronous).
-   **Data Processing**: Các script và service độc lập để chạy các pipeline thu thập và xử lý dữ liệu (ETL/ELT) theo lịch trình hoặc thời gian thực.
-   **Databases**: PostgreSQL để lưu trữ dữ liệu có cấu trúc, bền vững và Redis để lưu cache và dữ liệu streaming thời gian thực.

### Sơ đồ Triển khai

Hệ thống tuân theo sơ đồ triển khai dưới đây, với sự tách biệt rõ ràng giữa các thành phần.

![Deployment Architecture](doc/diagram/UML-deployment.png)

*Trong phạm vi đồ án, tất cả các thành phần được triển khai bằng Docker và Docker Compose để phục vụ mục đích phát triển và kiểm thử.*

### Tài liệu Dự án

Các tài liệu chi tiết khác về kiến trúc, thiết kế và các quyết định kỹ thuật có thể được tìm thấy trong thư mục `doc`.

---

## 🚀 Bắt đầu

### Yêu cầu Hệ thống

#### Môi trường Phát triển
- **Docker & Docker Compose**: 4.41.2+
- **Python**: 3.11+ (khuyến nghị sử dụng trong môi trường Conda để đảm bảo tương thích với các thư viện khoa học dữ liệu như TA-Lib)

#### Phiên bản Thành phần
- **PostgreSQL**: 15 (Image Alpine)
- **Redis**: 7 (Image Alpine)

#### Công cụ Hỗ trợ
- **DBeaver 25**: Dành cho các thao tác với cơ sở dữ liệu qua giao diện đồ họa.

### Cài đặt

#### 1. Clone Repository
```bash
git clone https://github.com/triet4p/itapia.git
cd itapia
```

#### 2. Cấu hình Biến môi trường
Dự án sử dụng một file `.env` duy nhất ở thư mục gốc chứa tất cả các biến môi trường cần thiết.

Tạo một file `.env` ở thư mục gốc từ file `.env.example` và điền các giá trị của bạn:
```ini
# Postgre
POSTGRES_USER=itapia_user
POSTGRES_PASSWORD=123456
POSTGRES_DB=stocks_db
POSTGRES_HOST=stocks_postgre_db
POSTGRES_PORT=5432

# Redis
REDIS_HOST=realtime_redis_db
REDIS_PORT=6379

# API GATEWAY
GATEWAY_HOST=api-gateway
GATEWAY_PORT=8000
GATEWAY_V1_BASE_ROUTE=/api/v1

# AI Service Quick
AI_QUICK_HOST=ai-service-quick
AI_QUICK_PORT=8000
AI_QUICK_V1_BASE_ROUTE=/api/v1

# Kaggle Secrets (cần thiết để AI Service tải mô hình)
KAGGLE_KEY=<your-kaggle-key>
KAGGLE_USERNAME=<your-kaggle-username>
```

---

## 📊 Cài đặt Pipeline Dữ liệu

### 1. Build Image
```bash
# Image cho các script xử lý dữ liệu
docker build -t itapia-data-processor:latest -f data_processing/Dockerfile .
```

### 2. Khởi động Cơ sở dữ liệu
```bash
# Khởi động PostgreSQL và Redis ở chế độ nền
docker-compose up -d stocks_postgre_db realtime_redis_db
```

### 3. Khởi tạo Cấu trúc Database
Sử dụng DBeaver hoặc dòng lệnh để kết nối tới database và thực thi các câu lệnh SQL trong `db/ddl.sql` để tạo các bảng cần thiết. Bạn cũng cần "seed" dữ liệu cho các bảng tĩnh như `exchanges` và `sectors` từ các file trong `db/seeds`.

### 4. Chạy Thu thập Dữ liệu Lô (Batch)
Các script này sẽ tự động lấy danh sách ticker từ CSDL để xử lý.
```bash
# Thu thập dữ liệu giá lịch sử
docker-compose run --rm batch-data-processor python scripts/fetch_daily_prices.py

# Thu thập dữ liệu tin tức liên quan (của từng cổ phiếu)
docker-compose run --rm batch-data-processor python scripts/fetch_relevant_news.py

# Thu thập tin tức vĩ mô (theo từ khóa)
docker-compose run --rm batch-data-processor python scripts/fetch_universal_news.py
```

*Các script sẽ tự động tìm ngày gần nhất đã lấy và chỉ thu thập dữ liệu mới. Bạn có thể thêm hoặc thay đổi các từ khóa tìm kiếm tin tức vĩ mô trong file [utils.py](./data_processing/scripts/utils.py).*

### 5. Chạy Thu thập Dữ liệu Thời gian thực
Service này sẽ tự động quét và chỉ lấy dữ liệu cho các cổ phiếu có thị trường đang mở cửa.
```bash
docker-compose up -d realtime-data-processor
```
---
## 🧠 Cài đặt AI Service & API Gateway

### 1. Build các Image
```bash
# Build AI service quick
docker build -t itapia-ai-service-quick:latest -f ai_service_quick/Dockerfile .

# Build API Gateway
docker build -t itapia-api-gateway:latest -f api_gateway/Dockerfile .
```

### 2. Khởi động các Dịch vụ
Đảm bảo các dịch vụ CSDL đang chạy, sau đó khởi động các service ứng dụng:
```bash
# Khởi động toàn bộ các service ứng dụng
docker-compose up -d ai-service-quick api-gateway
```
*Lưu ý: `ai-service-quick` có thể mất vài phút ở lần khởi động đầu tiên để tải về và cache các mô hình AI.*

### 3. Truy cập Tài liệu API
Khi các dịch vụ đang chạy, bạn có thể truy cập tài liệu OpenAPI (Swagger UI) để tương tác với các API:
- **API Gateway (Public Endpoints)**: **http://localhost:8000/docs**
- **AI Service Quick (Internal Endpoints)**: http://localhost:8001/docs

---

## 🗺️ Danh sách API

Tất cả các tương tác bên ngoài đều thông qua **API Gateway**.

### AI - Phân tích và Dự báo
-   `GET /api/v1/ai/quick/analysis/full/{ticker}`: Lấy báo cáo phân tích nhanh **đầy đủ** (JSON).
-   `GET /api/v1/ai/quick/analysis/technical/{ticker}`: Chỉ lấy báo cáo **Phân tích Kỹ thuật** (JSON).
-   `GET /api/v1/ai/quick/analysis/forecasting/{ticker}`: Chỉ lấy báo cáo **Dự báo** (JSON).
-   `GET /api/v1/ai/quick/analysis/news/{ticker}`: Chỉ lấy báo cáo **Phân tích Tin tức** (JSON).
-   `GET /api/v1/ai/quick/analysis/explanation/{ticker}`: Lấy bản tóm tắt phân tích dưới dạng **văn bản (plain-text)**, phù hợp cho người đọc.

### Prices - Dữ liệu Giá
-   `GET /api/v1/prices/daily/{ticker}`: Lấy dữ liệu giá lịch sử hàng ngày.
-   `GET /api/v1/prices/sector/daily/{sector}`: Lấy dữ liệu giá hàng ngày của cả một ngành.
-   `GET /api/v1/prices/intraday/last/{ticker}`: Lấy điểm dữ liệu giá mới nhất trong ngày.
-   `GET /api/v1/prices/intraday/history/{ticker}`: Lấy toàn bộ lịch sử giá trong ngày.

### News - Dữ liệu Tin tức
-   `GET /api/v1/news/relevants/{ticker}`: Lấy các tin tức liên quan trực tiếp đến một cổ phiếu.
-   `GET /api/v1/news/universal`: Lấy các tin tức vĩ mô theo từ khóa (truyền qua query params).

### Metadata - Dữ liệu Nền
-   `GET /api/v1/metadata/sectors`: Lấy danh sách tất cả các nhóm ngành được hỗ trợ.

---

## 📈 Quy trình Huấn luyện Mô hình

Do giới hạn tài nguyên, các quy trình huấn luyện và tối ưu hóa mô hình được thực hiện trên các nền tảng đám mây như Kaggle hoặc Google Colab.

#### 1. Chuẩn bị Dữ liệu Huấn luyện
`ai-service-quick` cung cấp một cơ chế để xuất dữ liệu đã được làm giàu (enriched data) ra file CSV, sẵn sàng cho việc huấn luyện.
```bash
# Tạo thư mục local nếu chưa có
mkdir -p ./ai_service_quick/local

# Chạy lệnh exec để kích hoạt script xuất dữ liệu
docker exec itapia-ai-service-quick-1 conda run -n itapia python -m app.orchestrator <SECTOR-CODE>
```
*File CSV sẽ được lưu trong thư mục `ai_service_quick/local/`.*

#### 2. Tải Dữ liệu và Huấn luyện trên Kaggle
-   Tạo một bộ dữ liệu mới trên [Kaggle Datasets](https://www.kaggle.com/datasets) và tải lên file CSV đã xuất.
-   Tạo một notebook Kaggle mới và sử dụng template có sẵn để huấn luyện, tối ưu hóa và lưu mô hình.
    -   [Kaggle Template Training Notebook](https://www.kaggle.com/code/trietp1253201581/itapia-training)
    -   [Local Template Training Notebook](./notebooks/itapia-training.ipynb)

#### 3. Tái sử dụng Mô hình
`ai-service-quick` được thiết kế để tự động tải về các phiên bản mô hình đã được huấn luyện và lưu trên Kaggle Datasets khi khởi động. Chi tiết có thể xem trong [model.py](./ai_service_quick/app/forecasting/model.py).

---

## 🔧 Cấu trúc Dự án
```
itapia/
├── api_gateway/             # Dịch vụ API Gateway (FastAPI)
├── ai_service_quick/        # Dịch vụ AI cho Quick Check (FastAPI, CPU)
├── data_processing/         # Các script và service xử lý dữ liệu (ETL)
├── db/                      # Schema DDL và dữ liệu seeds
├── doc/                     # Tài liệu chi tiết của dự án
├── shared/                  # Thư viện chung (shared library)
├── docker-compose.yml       # Cấu hình các dịch vụ Docker
├── .env.example             # File mẫu cho biến môi trường
└── README.md
```

---

## 📈 Các Tính năng Chính

- **AI Giải thích được (XAI)**: Các khuyến nghị đầu tư minh bạch với lý do rõ ràng và "bằng chứng" đi kèm.
- **Kiến trúc Hai cấp độ (Quick Check & Deep Dive)**: Cung cấp cả phân tích nhanh tức thời và phân tích sâu toàn diện.
- **Dữ liệu Thời gian thực**: Cập nhật giá và phân tích các động thái trong ngày.
- **Tối ưu hóa Tiến hóa (`Evo Agent` - Tương lai)**: Khả năng tự động tìm kiếm và tối ưu hóa các chiến lược giao dịch.

---

## 🤝 Đóng góp & Trích dẫn

Đây là một dự án đồ án tốt nghiệp. Mọi câu hỏi hoặc gợi ý, xin vui lòng tham khảo các tài liệu trong thư mục `doc`.

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