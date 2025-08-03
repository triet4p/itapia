
---

# **ITAPIA - Intelligent and Transparent AI-Powered Personal Investment Assistant**

ITAPIA (Intelligent and Transparent AI-Powered Personal Investment Assistant) is a graduate thesis project aimed at building an intelligent stock investment support platform, specifically designed for individual investors.

Unlike traditional "black box" tools, ITAPIA focuses on **Explainability (XAI)**, providing transparent recommendations, and has a long-term vision for the ability to **learn and co-evolve** with its users.

**Detailed Technical & Architectural Documentation**: **[itapia-mvp-v1.0.md](./doc/public/itapia-mvp-v1.0.md)** (Currently in Vietnamese)

**Vietnamese version of README**: [README.md](./README.md)

---

## 🏗️ System Architecture

The system is built on a microservices architecture, based on a robust `sharedlib` and a clear hierarchical Orchestrator structure.

-   **API Gateway** (`api_gateway`): The single entry point for all external communication, handling routing and request coordination to internal services.
-   **AI Service Quick** (`ai_service_quick`): The brain of the system, running on a CPU infrastructure. It contains the core AI modules and is responsible for the entire `Quick Check` process to generate analysis reports and recommendations.
-   **Data Processing** (`data_processing`): Independent services for running data collection and processing (ETL) pipelines in both scheduled (batch) and real-time modes.
-   **Data Seeds** (`data_seeds`): A one-off service to initialize the database with its schema (DDL) and initial data (including built-in rules).
-   **Databases**: PostgreSQL (with `JSONB`) for persistent, structured data (prices, news, rules) and Redis for caching and real-time streaming data.

### Deployment Diagram

![Deployment Architecture](doc/diagram/UML-deployment.png)

*For the scope of this project, all components are deployed using Docker and Docker Compose.*

---

## 🚀 Quick Start

### System Requirements
- **Docker & Docker Compose**
- **Python 3.11+**
- **Git**

### Installation & Execution Flow

**Step 1: Clone Repository and Configure Environment**
```bash
git clone https://github.com/triet4p/itapia.git
cd itapia
# Create a .env file from the template and fill in your Kaggle credentials
cp .env.template .env
```

**Step 2: Build All Docker Images**
*This command builds images for `data-processing`, `data-seeds`, `ai-service-quick`, and `api-gateway`.*
```bash
docker-compose build
```

**Step 3: Initialize and Seed the Database**
*This command starts the databases, creates the tables, and populates them with built-in rules.*
```bash
# Start the databases in the background
docker-compose up -d stocks_postgre_db realtime_redis_db

# Wait for about 10-15 seconds for the databases to fully initialize
sleep 15 

# Run the seeding service, which will exit automatically upon completion
docker-compose up data-seeds
```

**Step 4: Start the Entire System**
```bash
# Start the background data processing services and the main application services
docker-compose up -d
```

*Note: `ai-service-quick` may take a few minutes on its first launch to download and cache the AI models from Kaggle/Hugging Face.*

**Step 5: Access the System**
- **API Gateway (Public API Documentation)**: **http://localhost:8000/docs**
- **AI Service Quick (Internal API Documentation)**: http://localhost:8001/docs

---

## 🗺️ API Endpoints

All external interactions are handled through the **API Gateway**. Below are the main endpoint groups.

*(The `/api/v1` prefix applies to all)*

### **Advisor - Recommendations & Inference (Top Level)**
*   `GET /advisor/quick/{ticker}`: Get the **full** recommendation report (JSON). **This is the main endpoint.**
*   `GET /advisor/quick/{ticker}/explain`: Get a **natural language explanation** of the recommendation report.

### **Analysis - Detailed Analysis Data**
*   `GET /analysis/quick/{ticker}`: Get the composite analysis report (Technical, Forecasting, News).
*   `GET /analysis/quick/{ticker}/technical`: Get only the Technical Analysis report.
*   `GET /analysis/quick/{ticker}/forecasting`: Get only the Forecasting report.
*   `GET /analysis/quick/{ticker}/news`: Get only the News Analysis report.

### **Rules - Rule Management & Explanation**
*   `GET /rules`: Get a summary list of all built-in rules.
*   `GET /rules/{rule_id}`: Get the detailed structure (JSON logic tree) of a specific rule.
*   `GET /rules/{rule_id}/explain`: Get a natural language explanation of a rule's logic.

### **Market Data - Raw Market Data**
*   `GET /market/tickers/{ticker}/prices/daily`: Get historical daily price data.
*   `GET /market/tickers/{ticker}/prices/intraday?latest_only=True/False`: Get the latest intraday price data point.
*   `GET /market/tickers/{ticker}/news`: Get news articles relevant to a stock.
*   ... and other data endpoints.

### **Metadata - Foundational Data**
*   `GET /metadata/sectors`: Get the list of all supported industry sectors.

---

## 📈 Model Training Pipeline

Due to resource constraints, the model training and optimization processes are performed on cloud platforms like Kaggle/Colab.
`ai-service-quick` provides a mechanism to export enriched data, ready for training.

**How to export data for the 'TECH' sector:**
```bash
docker-compose exec ai-service-quick conda run -n itapia python -m app.analysis.orchestrator TECH
```
*The CSV file will be saved in the `ai_service_quick/local/` directory.*

Details about the training process can be found in the [Local Training Notebook](./notebooks/itapia-training.ipynb).

---

## 🔧 Project Structure
```
itapia/
├── api_gateway/        # API Gateway service (FastAPI)
├── ai_service_quick/   # AI service for Quick Check (FastAPI, CPU)
├── data_processing/    # Data collection pipelines (ETL)
├── data_seeds/         # Database initialization scripts
├── doc/                # Detailed project documentation
├── shared/             # Shared library
├── docker-compose.yml  # Docker services configuration
└── README.md
```

---

## 📈 Key Features (MVP v1.0)

- **Explainable AI (XAI)**: Every recommendation comes with "evidence" in the form of a list of triggered rules, providing complete transparency.
- **Hierarchical Orchestrator Architecture**: A clean backend architecture (`CEO` -> `Deputy` -> `Department Head`) that makes the system maintainable and scalable.
- **Robust Rule Engine**: An internal rule "language" based on Symbolic Expression Trees and Strongly-Typed Genetic Programming (STGP) principles, serving as a foundation for both expert rules and future evolutionary algorithms.
- **Multi-faceted Analysis**: Combines signals from Technical Analysis, Machine Learning Forecasting, and News Analysis into a single, comprehensive report.
- **Comprehensive API System**: Provides endpoints from high-level (recommendations) to low-level (raw data), serving a variety of use cases.

---

## 🤝 Contribution & Citation
This is a graduate thesis project. For any questions or suggestions, please refer to the **[Detailed Technical & Architectural Documentation](./doc/public/itapia-mvp-v1.0.md)**.

### Citation

If you use this work in your research, please cite it as:
```txt
[Le, Minh Triet]. (2025). ITAPIA: An Intelligent and Transparent AI-Powered Personal Investment Assistant. 
Graduate Thesis, Hanoi University of Science and Technology, Vietnam.```
**Model Citation:**
This project utilizes a fine-tuned financial sentiment analysis model provided by Ankit Aglawe.
```bibtex
@misc{AnkitAI_2024_financial_sentiment_model,
  title={DistilBERT Fine-Tuned for Financial Sentiment Analysis},
  author={Ankit Aglawe},
  year={2024},
  howpublished={\url{https://huggingface.co/AnkitAI/distilbert-base-uncased-financial-news-sentiment-analysis}},
}
```
For commercial purposes or collaboration, please contact `trietlm0306@gmail.com`.

---

## 📄 License

This project was developed as part of a graduate thesis. The source code is available for academic and educational purposes.