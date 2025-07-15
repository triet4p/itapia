Of course! Here is a professionally translated and structured English version of your `README.md` file, perfect for a `README-en.md`.

It captures all the technical depth and architectural decisions we've discussed, presenting them clearly for an international audience.

---

### **README-en.md**

# ITAPIA - Intelligent and Transparent AI-Powered Personal Investment Assistant

ITAPIA (Intelligent and Transparent AI-Powered Personal Investment Assistant) is a graduation thesis project aimed at building an intelligent stock investment support platform. The project is specifically designed for individual investors, particularly those with limited capital who prioritize risk management and seek to understand the reasoning behind AI-driven investment recommendations.

Unlike traditional "black box" tools, ITAPIA's core philosophy centers on **Explainability (XAI)**, **cost-effectiveness**, and the ability to **learn and co-evolve** with its users.

---

## 🏗️ System Architecture

The system is built on a microservices-based architecture, comprising the following core components:

-   **API Gateway** (`api_gateway`): Acts as the single entry point for all client requests, handling authentication, authorization, and request orchestration.
-   **AI Service Quick** (`ai_service_quick`): A CPU-based service responsible for fast, synchronous analysis and forecasting pipelines (the "Quick Check" process).
-   **AI Service Deep** (Future Work): A GPU-based service designed for complex, time-consuming AI/LLM tasks (the "Deep Dive" process).
-   **Data Processing**: A set of independent scripts for running scheduled ETL (Extract, Transform, Load) pipelines.
-   **Databases**: PostgreSQL for persistent, structured data storage and Redis for caching and real-time intraday data.

### Deployment Diagram

The system follows the deployment diagram below, which illustrates the clear separation of components and their interactions.

![Deployment Architecture](doc/diagram/UML-deployment.png)

Within the scope of this project, all components are containerized using Docker for development and testing purposes.

### Project Documentation

Further detailed project documentation can be found in the `doc` directory.

---

## 🚀 Getting Started

### System Requirements

#### Development Environment
- **Docker**: 4.41.2+
- **Python**: 3.11+ (Recommended for Conda environment and TA-Lib compatibility)

#### Component Versions
- **PostgreSQL**: 15 (Alpine image)
- **Redis**: 7 (Alpine image)

#### Supporting Tools
- **DBeaver 25**: Recommended for GUI-based database operations.

### Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/triet4p/itapia.git
cd itapia
```

#### 2. Configure Environment Variables
The project uses a single `.env` file in the root directory for all necessary environment variables.

Create a `.env` file in the project root with the following content:
```ini
# PostgreSQL
POSTGRES_USER=itapia_user
POSTGRES_PASSWORD=123456
POSTGRES_DB=stocks_db
POSTGRES_HOST=stocks_postgre_db
POSTGRES_PORT=5432

# Redis
REDIS_HOST=realtime_redis_db
REDIS_PORT=6379

# API Gateway
GATEWAY_HOST=api-gateway
GATEWAY_PORT=8000
GATEWAY_V1_BASE_ROUTE=/api/v1

# AI Service Quick
AI_QUICK_HOST=ai-service-quick
AI_QUICK_PORT=8000
AI_QUICK_V1_BASE_ROUTE=/api/v1
```

---

## 📊 Data Pipeline Setup

### 1. Build Required Images
```bash
# Image for data processing scripts
docker build -t itapia-data-processor:latest data_processing
```

### 2. Start Database Services
- Start PostgreSQL in detached mode:
```bash
docker-compose up -d stocks_postgre_db
```
- Start the Redis (In-memory) container:
```bash
docker-compose up -d realtime_redis_db
```

### 3. Initialize Database Tables
Use DBeaver or the command line to connect to the database and execute the SQL commands in `db/ddl.sql` to create the necessary tables in PostgreSQL. You will also need to seed the static lookup tables, such as `exchanges` and `sectors`.

### 4. Run Batch Data Collection Scripts
These scripts will automatically fetch the list of tickers from the database.

```bash
# Collect historical price data
docker-compose run --rm batch-data-processor python scripts/fetch_history.py

# Collect news data
docker-compose run --rm batch-data-processor python scripts/fetch_news.py
```
The scripts will automatically fetch OHLCV data from the most recent date (defaulting to `2018-01-01` for the initial run) for the 92 configured stocks, restructure the response, fill missing values, and load it into the database.

### 5. Run Real-time Data Collection
This service automatically scans and fetches data only for stocks whose markets are currently open.
```bash
docker-compose up -d realtime-data-processor
```

---

## 🤖 AI & API Services Setup

### 1. Build Service Images
```bash
# Build the API Gateway
docker build -t itapia-api-gateway:latest api_gateway

# Build the AI Service Quick
docker build -t itapia-ai-service-quick:latest ai_service_quick
```

### 2. Start Application Services
Ensure the database services are running, then start the application services:
```bash
docker-compose up -d api-gateway ai-service-quick
```

### 3. Access API Documentation
Once the services are running, you can access:
- **API Gateway Docs**: http://localhost:8000/docs
- **AI Service Quick Docs**: http://localhost:8001/docs
- **API Gateway Base URL**: http://localhost:8000/api/v1

### 4. Key Endpoints
- **GET `/api/v1/metadata/sectors`**: Get a list of all supported industry sectors.
- **GET `/api/v1/prices/daily/sector/{sector_code}`**: Get daily price data for an entire sector.
- **GET `/api/v1/prices/daily/{ticker}`**: Get historical price data for a single stock.
- **POST `/api/v1/ai/quick/analysis/full/{ticker}`**: **(In AI Service)** Request a full, quick analysis for a stock.

---

## 🔧 Project Structure

```
itapia/
├── api_gateway/             # FastAPI-based API Gateway service
│   ├── app/
│   └── Dockerfile
├── ai_service_quick/        # AI Service for Quick Check (FastAPI, CPU)
│   ├── app/
│   │   ├── common/
│   │   ├── core/
│   │   ├── data_prepare/
│   │   └── technical_analysis/
│   └── Dockerfile
├── data_processing/         # Data processing scripts (ETL)
│   ├── scripts/
│   └── ...
├── db/                      # Database schema (DDL) and migrations
├── doc/                     # Project documentation and diagrams
├── docker-compose.yml       # Docker services configuration
├── .env                     # (Must be created) Environment variables
└── README.md
```

---

## 📈 Key Features

- **Explainable AI (XAI)**: Transparent investment recommendations with clear reasoning and supporting evidence.
- **Tiered Architecture (Quick Check & Deep Dive)**: Provides both instant, high-level analysis and comprehensive, in-depth insights.
- **Multi-Market Support**: The platform is designed to handle data from various markets with different timezones and currencies.
- **Real-time Data**: Live stock price updates and intraday market monitoring.
- **Evolutionary Optimization (`Evo Agent`)**: A powerful component for automatically discovering and optimizing trading strategies.

---

## 🤝 Contributing

This is a graduation thesis project. For questions or suggestions, please refer to the project documentation in the `doc` directory.

---

## 📄 License

This project is developed as part of a graduation thesis. The code is available for academic and educational use. For detailed license terms, see the [LICENSE](LICENSE) file.

### Citation
If you use this work in your research, please cite:
```txt
[Le Minh Triet]. (2025). ITAPIA: Intelligent and Transparent AI-Powered Personal Investment Assistant. 
Graduation Thesis, Hanoi University of Science and Technology (HUST), Vietnam.
```
For commercial use or collaboration inquiries, please contact `trietlm0306@gmail.com`.