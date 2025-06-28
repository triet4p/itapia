# ITAPIA - Intelligent and Transparent AI-Powered Personal Investment Assistant

ITAPIA (Intelligent and Transparent AI-Powered Personal Investment Assistant) is a graduation thesis project aimed at building an intelligent stock investment support platform. The project is specifically designed for individual investors with limited capital who prioritize risk management and seek to understand AI-driven investment recommendations.

Unlike traditional "black box" tools, ITAPIA focuses on explainability, low cost, and the ability to learn and evolve alongside its users.

---

## 🏗️ System Architecture

The system is built using a simplified microservices architecture, comprising the following core components:

- **Frontend**: React-based user interface containing client-side personalization logic
- **API Service** (CPU-based): Acts as API Gateway, handling standard business logic
- **AI Service** (GPU-based): Responsible for running heavy AI/LLM models
- **Data Processing**: Independent scripts for running scheduled ETL pipelines
- **Databases**: PostgreSQL for persistent data and Redis for caching & real-time data

### Deployment Architecture

The system follows the deployment diagram shown below:

![Deployment Architecture](doc/ITAPIA_deployment.png)

Within the project scope, all components are deployed using Docker for development and testing purposes.

### Project Documentation

Additional project documentation can be found in the `doc` directory.

---

## 🚀 Getting Started

### System Requirements

#### Development Environment
- **Docker**: 4.41.2+
- **Python**: 3.11+

#### Component Versions
- **PostgreSQL**: 15 (Alpine image)

#### Supporting Tools
- **DBeaver 25**: For GUI-based database operations

### Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/trietp1253201581/itapia.git
cd itapia
```

#### 2. Configure Environment Variables
This project uses a single `.env` file in the root directory containing all necessary environment variables.

Create a `.env` file in the project root with the following content:
```ini
POSTGRES_USER=itapia_user
POSTGRES_PASSWORD=123456
POSTGRES_DB=stocks_db
POSTGRES_HOST=stocks_postgre_db
POSTGRES_PORT=5432
```

---

## 📊 Data Pipeline Setup

### 1. Build Required Images
```bash
docker build -t itapia-data-processor data_processing
```

### 2. Start Database Services
- Start PostgreSQL in detached mode:
```bash
docker-compose up -d stocks_postgre_db
```

- Start Redis (In-memory) container:
```bash
docker-compose up -d realtime_db
```

### 3. Initialize Database Tables
Use DBeaver or command line to connect to the database and execute the SQL commands in `db/create_table.sql` to create the necessary tables in PostgreSQL.

### 4. Run Batch Data Collection Scripts
To collect data for a specific region (e.g., americas), run the following commands:

```bash
# Historical price data
docker-compose run --rm batch-data-processor python scripts/fetch_history.py americas

# News data
docker-compose run --rm batch-data-processor python scripts/fetch_news.py americas
```

**Supported Regions:**
- `americas`
- `europe` 
- `asia_pacific`

The scripts will automatically fetch OHLCV data from the most recent date (defaults to `2018-01-01` for initial run) for the configured stocks (89 stocks - see [tickers](data_processing/scripts/utils.py)), restructure the response, fill missing values, and load into the database.

### 5. Run Real-time Data Collection
To collect real-time data (current stock prices) for all regions, run:
```bash
docker-compose run --rm realtime-data-processor
```

---

## 🔧 Project Structure

```
itapia/
├── data_processing/          # Data processing scripts and utilities
│   ├── scripts/             # ETL pipeline scripts
│   └── ...
├── db/                      # Database schema and migrations
├── doc/                     # Project documentation
├── docker-compose.yml       # Docker services configuration
├── .env                     # Environment variables (create this)
└── README.md               # Project documentation
```

---

## 🛠️ Development Workflow

1. **Database Setup**: Initialize PostgreSQL and Redis containers
2. **Schema Creation**: Run database schema creation scripts
3. **Data Collection**: Execute batch data collection for historical data
4. **Real-time Processing**: Start real-time data collection services
5. **Development**: Begin application development with populated data

---

## 📈 Key Features

- **Explainable AI**: Transparent investment recommendations with clear reasoning
- **Risk Management**: Built-in risk assessment and management tools
- **Cost-Effective**: Designed for investors with limited capital
- **Multi-Region Support**: Covers Americas, Europe, and Asia-Pacific markets
- **Real-time Data**: Live stock price updates and market monitoring
- **News Integration**: Relevant financial news collection and analysis

---

## 🤝 Contributing

This is a graduation thesis project. For questions or suggestions, please refer to the project documentation in the `doc` directory.

---

## 📄 License

This project is developed as part of an academic graduation thesis. Please refer to the specific license terms in the repository.