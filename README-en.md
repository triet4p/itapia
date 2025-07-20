# ITAPIA - Intelligent and Transparent AI-Powered Personal Investment Assistant

ITAPIA (Intelligent and Transparent AI-Powered Personal Investment Assistant) is a graduation thesis project aimed at building an intelligent stock investment support platform. The project is specifically designed for individual investors with limited capital, who prioritize risk management and wish to clearly understand the investment recommendations provided by AI.

Unlike traditional "black box" tools, ITAPIA focuses on **Explainability (XAI)**, **low cost**, and the ability to **learn and co-evolve** with the user.

---

## 🏗️ System Architecture

The system is built on a microservices architecture, comprising the following core components:

-   **API Gateway** (`api_gateway`): Acts as the single entry point, handling authentication and orchestrating requests to internal services.
-   **AI Service Quick** (`ai_service_quick`): Runs on CPU infrastructure, responsible for fast analysis and forecasting processes (Quick Check).
-   **AI Service Deep** (Future): Will run on GPU infrastructure, dedicated to complex AI/LLM tasks (Deep Dive).
-   **Data Processing**: Independent scripts to run scheduled data collection and processing pipelines (ETL).
-   **Databases**: PostgreSQL for persistent data storage and Redis for caching and real-time data.

### Deployment Diagram

The system follows the deployment diagram below, with a clear separation between components.

![Deployment Architecture](doc/diagram/UML-deployment.png)

Within the scope of this thesis project, all components are deployed using Docker for development and testing purposes.

### Project Documentation

More detailed documentation about the project can be found in the `doc` directory.

---

## 🚀 Getting Started

### Prerequisites

#### Development Environment
- **Docker**: 4.41.2+
- **Python**: 3.11+ (recommended for the Conda environment and TA-Lib compatibility)

#### Component Versions
- **PostgreSQL**: 15 (Alpine Image)
- **Redis**: 7 (Alpine Image)

#### Auxiliary Tools
- **DBeaver 25**: For interacting with the database through a GUI.

### Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/triet4p/itapia.git
cd itapia
```

#### 2. Configure Environment Variables
The project uses a single `.env` file in the root directory for all necessary environment variables.

Create a file named `.env` in the root directory with the following content:
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

# Kaggle Secrets
KAGGLE_KEY=<your-kaggle-key>
KAGGLE_USERNAME=<your-kaggle-username>
```

---

## 📊 Data Pipeline Setup

### 1. Build Necessary Images
```bash
# Image for data processing scripts
docker build -t itapia-data-processor:latest -f data_processing/Dockerfile .
```

### 2. Start Database Services
- Start PostgreSQL in detached mode:
```bash
docker-compose up -d stocks_postgre_db
```

- Start the Redis container (In-memory):
```bash
docker-compose up -d realtime_redis_db
```

### 3. Initialize Database Tables
Use DBeaver or the command line to connect to the database and execute the SQL commands in `db/ddl.sql` to create the necessary tables in PostgreSQL. You will also need to "seed" data for static tables like `exchanges` and `sectors`.

### 4. Run Batch Data Collection Scripts
These scripts will automatically fetch the list of tickers from the database to process.

```bash
# Collect historical price data
docker-compose run --rm batch-data-processor python scripts/fetch_daily_prices.py

# Collect news data
docker-compose run --rm batch-data-processor python scripts/fetch_relevant_news.py
```
The scripts will automatically find the most recent date collected and only fetch new data for the 92 configured stocks.

### 5. Run Real-time Data Collection
This service will automatically scan and fetch data only for stocks whose markets are currently open.
```bash
docker-compose up -d realtime-data-processor
```

---

## 🤖 API Gateway Setup

### 1. Build the Image
```bash
# Build API Gateway
docker build -t itapia-api-gateway:latest -f api_gateway/Dockerfile .
```

### 2. Start the Services
Ensure the database services are running, then start the application service:
```bash
docker-compose up -d api-gateway
```

### 3. Access API Documentation
With the services running, you can access:
- **API Gateway Docs**: http://localhost:8000/docs
- **API Gateway Base URL**: http://localhost:8000/api/v1

### 4. Key Endpoints
- **GET /api/v1/metadata/sectors**: Get the list of all sectors.
- **GET /api/v1/prices/sector/daily/{sector_code}**: Get daily price data for an entire sector.
- **GET /api/v1/prices/daily/{ticker}**: Get historical price data for a single stock.
- **GET /api/v1/prices/intraday/last/{ticker}**: Get the latest intraday price for a stock.
- **GET /api/v1/prices/intraday/history/{ticker}**: Get intraday prices stored for the last 1-2 days.

---

## 🧠 AI Service Quick Setup

### 1. Build the Image
```bash
# Build AI Service Quick
docker build -t itapia-ai-service-quick:latest -f ai_service_quick/Dockerfile .
```

### 2. Start the Services
Ensure the database services are running, then start the application service:
```bash
docker-compose up -d ai-service-quick
```

### 3. Access API Documentation
With the services running, you can access:
- **AI Service Quick Docs**: http://localhost:8001/docs
- **AI Service Quick Base URL**: http://localhost:8001/api/v1

### 4. Key Endpoints
- **GET /api/v1/ai/quick/analysis/full/{ticker}**: Request a complete quick analysis for a stock.

### 5. Training Process on Kaggle
Due to local machine and Docker resource limitations, the training processes should be executed on platforms with powerful resources like Kaggle or Google Colab.

The following is a guide for training on Kaggle, which is similar to Colab.

- **Note**: Each Kaggle session (12 hours) will be used to train models for 3 tasks within the same sector:
  - Triple Barrier Classification.
  - 5-days Distribution Regression.
  - 20-days Distribution Regression.

#### 5.1. Data Preparation
Since we cannot connect directly to the Docker Network from the Internet to fetch data from the API Gateway, we will first retrieve and save it locally, then upload it to Kaggle Datasets.

The default temporary storage directory is `/ai-service-quick/local`. You can create it beforehand to avoid unexpected errors.

Next, export the CSV data using the command:
```bash
docker exec -it itapia-ai-service-quick-1 conda run --no-capture-output -n itapia python -m app.orchestrator.orchestrator <SECTOR-CODE>
```
- **Note**: To get the correct sector code, use the API to view the list of sectors.

#### 5.2. Upload Data to Kaggle Datasets
Create a new Dataset and upload the files from the temporary directory.
[Kaggle Datasets](https://www.kaggle.com/datasets)

#### 5.3. Create and Run a Notebook on Kaggle
Create a notebook on Kaggle to run the model training and optimization scripts. A template for the notebook can be found at:
[Template Training Notebook](https://www.kaggle.com/code/trietp1253201581/itapia-training) or [Local Template Training Notebook](./notebooks/itapia-training.ipynb)

#### 5.4. Reusing Models
The source code provides methods to register and load models managed by Kaggle. See [model.py](./ai_service_quick/app/forecasting/model.py) for details.

- **Note**: When you create a `ForecastingModel` for training, the **`Model Slug`** (the access path for the model on Kaggle) will be generated automatically from a template.
    ```python
    MODEL_SLUG_TEMPLATE = 'itapia-final-{id}'
    ```
    where `id` is typically formed by the `name` of the `ForecastingModel` and the `task_id` of the `ForecastingTask` it solves. For easier management, you should name the `model` after the algorithm it uses and use the predefined template for the `task_id` from [config.py](./ai_service_quick/app/core/config.py):
    ```python
    TASK_ID_SECTOR_TEMPLATE = '{problem}-{sector}'
    ```
    where `problem` is the name of the problem being solved, which includes:
    - `clf-triple-barrier`
    - `reg-5d-dis`
    - `reg-20d-dis`

---

## 🔧 Project Structure

```
itapia/
├── api_gateway/             # API Gateway Service (FastAPI)
│   ├── app/
│   └── Dockerfile
├── ai_service_quick/        # AI Service for Quick Check (FastAPI, CPU)
│   ├── app/
│   │   ├── common/
│   │   ├── core/
│   │   ├── data_prepare/
│   │   └── technical/
│   │   └── forecasting/
│   └── Dockerfile
├── data_processing/         # Data processing scripts (ETL)
│   ├── scripts/
│   └── ...
├── db/                      # Schema and migrations
├── doc/                     # Project documentation
├── docker-compose.yml       # Docker services configuration
├── .env                     # (Must be created) Environment variables
└── README.md
```

---

## 📈 Key Features

- **Explainable AI (XAI)**: Transparent investment recommendations with clear reasoning and accompanying "evidence".
- **Two-Tier Architecture (Quick Check & Deep Dive)**: Provides both instant, quick analysis and comprehensive, in-depth analysis.
- **Multi-Market Support**: The platform is designed to handle data from multiple markets with different timezones and currencies. Although currently scoped to the US market, the data-agnostic framework design allows for easy expansion later.
- **Real-time Data**: Updates prices and analyzes intraday market movements.
- **Evolutionary Optimization (`Evo Agent`)**: Capable of automatically discovering and optimizing trading strategies.

---

## 🤝 Contribution

This is a graduation thesis project. For any questions or suggestions, please refer to the documents in the `doc` directory.

---

## 📄 License

This project is developed as part of a graduation thesis. The source code is available for academic and educational purposes.

### Citation
If you use this work in your research, please cite it as:
```txt
[Le, Minh Triet]. (2025). ITAPIA: Intelligent and Transparent AI-Powered Personal Investment Assistant. 
Graduation Thesis, Hanoi University of Science and Technology, Vietnam.
```
For commercial purposes or collaboration, please contact `trietlm0306@gmail.com`.