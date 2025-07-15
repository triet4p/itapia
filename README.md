# ITAPIA - Trợ lý Đầu tư Cá nhân Thông minh và Minh bạch dựa trên AI

ITAPIA (Intelligent and Transparent AI-Powered Personal Investment Assistant) là một dự án đồ án tốt nghiệp với mục tiêu xây dựng một nền tảng hỗ trợ đầu tư chứng khoán thông minh. Dự án được thiết kế đặc biệt cho các nhà đầu tư cá nhân với vốn hạn chế, ưu tiên việc quản lý rủi ro và mong muốn hiểu rõ các khuyến nghị đầu tư do AI đưa ra.

Khác với các công cụ "hộp đen" truyền thống, ITAPIA tập trung vào **khả năng giải thích (Explainability)**, **chi phí thấp**, và khả năng **học hỏi, đồng phát triển** cùng người dùng.

**English version of README**: [README-en.md](./README-en.md)

---

## 🏗️ Kiến trúc Hệ thống

Hệ thống được xây dựng theo kiến trúc microservices, bao gồm các thành phần cốt lõi sau:

-   **API Gateway** (`api_gateway`): Đóng vai trò là cổng giao tiếp duy nhất, xử lý xác thực và điều phối request đến các dịch vụ nội bộ.
-   **AI Service Quick** (`ai_service_quick`): Chạy trên hạ tầng CPU, chịu trách nhiệm cho các quy trình phân tích và dự báo nhanh (Quick Check).
-   **AI Service Deep** (Tương lai): Chạy trên hạ tầng GPU, dành cho các tác vụ AI/LLM phức tạp (Deep Dive).
-   **Data Processing**: Các script độc lập để chạy các pipeline thu thập và xử lý dữ liệu theo lịch trình (ETL).
-   **Databases**: PostgreSQL để lưu trữ dữ liệu bền vững và Redis để lưu cache và dữ liệu thời gian thực.

### Sơ đồ Triển khai

Hệ thống tuân theo sơ đồ triển khai dưới đây, với sự tách biệt rõ ràng giữa các thành phần.

![Deployment Architecture](doc/diagram/UML-deployment.png)`

Trong phạm vi đồ án, tất cả các thành phần được triển khai bằng Docker để phục vụ mục đích phát triển và kiểm thử.

### Tài liệu Dự án

Các tài liệu chi tiết khác về dự án có thể được tìm thấy trong thư mục `doc`.

---

## 🚀 Bắt đầu

### Yêu cầu Hệ thống

#### Môi trường Phát triển
- **Docker**: 4.41.2+
- **Python**: 3.11+ (khuyến nghị cho môi trường Conda và tương thích với TA-Lib)

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

Tạo một file `.env` ở thư mục gốc với nội dung sau:
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
```

---

## 📊 Cài đặt Pipeline Dữ liệu

### 1. Build các Image cần thiết
```bash
# Image cho các script xử lý dữ liệu
docker build -t itapia-data-processor:latest data_processing
```

### 2. Khởi động các Dịch vụ Cơ sở dữ liệu
- Khởi động PostgreSQL ở chế độ detached:
```bash
docker-compose up -d stocks_postgre_db
```

- Khởi động container Redis (In-memory):
```bash
docker-compose up -d realtime_redis_db
```

### 3. Khởi tạo Bảng trong Database
Sử dụng DBeaver hoặc dòng lệnh để kết nối tới database và thực thi các câu lệnh SQL trong `db/ddl.sql` để tạo các bảng cần thiết trong PostgreSQL. Bạn cũng cần "seed" dữ liệu cho các bảng tĩnh như `exchanges` và `sectors`.

### 4. Chạy các Script Thu thập Dữ liệu Lô (Batch)
Các script này sẽ tự động lấy danh sách ticker từ CSDL để xử lý.

```bash
# Thu thập dữ liệu giá lịch sử
docker-compose run --rm batch-data-processor python scripts/fetch_history.py

# Thu thập dữ liệu tin tức
docker-compose run --rm batch-data-processor python scripts/fetch_news.py
```
Các script sẽ tự động tìm ngày gần nhất đã lấy và chỉ thu thập dữ liệu mới cho 92 cổ phiếu đã được cấu hình.

### 5. Chạy Thu thập Dữ liệu Thời gian thực
Dịch vụ này sẽ tự động quét và chỉ lấy dữ liệu cho các cổ phiếu có thị trường đang mở cửa.
```bash
docker-compose up -d realtime-data-processor
```

---

## 🤖 Dịch vụ AI & API Setup

### 1. Build các Image
```bash
# Build API Gateway
docker build -t itapia-api-gateway:latest api_gateway

# Build AI Service Quick
docker build -t itapia-ai-service-quick:latest ai_service_quick
```

### 2. Khởi động các Dịch vụ
Đảm bảo các dịch vụ CSDL đang chạy, sau đó khởi động các service ứng dụng:
```bash
docker-compose up -d api-gateway ai-service-quick
```

### 3. Truy cập Tài liệu API
Khi các dịch vụ đang chạy, bạn có thể truy cập:
- **Tài liệu API Gateway**: http://localhost:8000/docs
- **Tài liệu AI Service Quick**: http://localhost:8001/docs
- **URL cơ sở của API Gateway**: http://localhost:8000/api/v1

### 4. Các Endpoint chính
- **GET /api/v1/metadata/sectors**: Lấy danh sách tất cả các nhóm ngành.
- **GET /api/v1/prices/daily/sector/{sector_code}**: Lấy dữ liệu giá hàng ngày cho cả một ngành.
- **GET /api/v1/prices/daily/{ticker}**: Lấy dữ liệu giá lịch sử cho một cổ phiếu.
- **POST /api/v1/ai/quick/analysis/full/{ticker}**: **(Trong AI Service)** Yêu cầu một phân tích nhanh hoàn chỉnh cho một cổ phiếu.

---

## 🔧 Cấu trúc Dự án

```
itapia/
├── api_gateway/             # Dịch vụ API Gateway (FastAPI)
│   ├── app/
│   └── Dockerfile
├── ai_service_quick/        # Dịch vụ AI cho Quick Check (FastAPI, CPU)
│   ├── app/
│   │   ├── common/
│   │   ├── core/
│   │   ├── data_prepare/
│   │   └── technical_analysis/
│   └── Dockerfile
├── data_processing/         # Các script xử lý dữ liệu (ETL)
│   ├── scripts/
│   └── ...
├── db/                      # Schema và migrations
├── doc/                     # Tài liệu dự án
├── docker-compose.yml       # Cấu hình các dịch vụ Docker
├── .env                     # (Cần tạo) Biến môi trường
└── README.md
```

---

## 📈 Các Tính năng Chính

- **AI Giải thích được (XAI)**: Các khuyến nghị đầu tư minh bạch với lý do rõ ràng và "bằng chứng" đi kèm.
- **Kiến trúc Hai cấp độ (Quick Check & Deep Dive)**: Cung cấp cả phân tích nhanh tức thời và phân tích sâu toàn diện.
- **Hỗ trợ Đa thị trường**: Nền tảng được thiết kế để xử lý dữ liệu từ nhiều thị trường với các múi giờ và tiền tệ khác nhau.
- **Dữ liệu Thời gian thực**: Cập nhật giá và phân tích các động thái trong ngày.
- **Tối ưu hóa Tiến hóa (`Evo Agent`)**: Khả năng tự động tìm kiếm và tối ưu hóa các chiến lược giao dịch.

---

## 🤝 Đóng góp

Đây là một dự án đồ án tốt nghiệp. Mọi câu hỏi hoặc gợi ý, xin vui lòng tham khảo các tài liệu trong thư mục `doc`.

---

## 📄 Giấy phép

Dự án này được phát triển như một phần của đồ án tốt nghiệp. Mã nguồn có sẵn cho các mục đích học thuật và giáo dục.

### Trích dẫn
Nếu bạn sử dụng công trình này trong nghiên cứu của mình, xin vui lòng trích dẫn:
```txt
[Lê Minh Triết]. (2025). ITAPIA: Trợ lý Đầu tư Cá nhân Thông minh và Minh bạch dựa trên Trí tuệ Nhân tạo. 
Đồ án Tốt nghiệp, Đại học Bách khoa Hà Nội, Việt Nam.
```
Đối với mục đích thương mại hoặc hợp tác, xin vui lòng liên hệ `trietlm0306@gmail.com`.