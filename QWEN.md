# Qwen Code Memory for ITAPIA Project

## Project Overview
- **Name**: ITAPIA (Intelligent & Transparent AI-Powered Personal Investment Assistant)
- **Type**: Graduate thesis project
- **Status**: In Development
- **Core Philosophy**: Transparency and Explainability (XAI) in AI-powered investment advice

## Tech Stack
- **Backend**: Python, FastAPI, Docker, PostgreSQL, Redis
- **Frontend**: Vue.js 3 with TypeScript, Vuetify
- **AI/ML**: Scikit-learn, BERT, TALib
- **Microservices**: Multi-service architecture with Docker Compose

## Key Services
1. **api-gateway**: Main entry point (port 8000)
2. **ai-service-quick**: AI service (port 8001)
3. **evo-worker**: Evolutionary worker service (port 8002)
4. **data_processing**: Batch and real-time data processing
5. **data_seeds**: Data seeding service
6. **Database**: PostgreSQL (port 5432)
7. **Cache**: Redis (port 6379)

## Project Structure
```
itapia/
├── backend/            # All microservices and Docker config
│   ├── api_gateway/    # Main API gateway service
│   ├── ai_service_quick/ # AI service
│   ├── data_processing/ # Data processing scripts
│   ├── data_seeds/     # Data seeding utilities
│   ├── evo_worker/     # Evolutionary algorithms worker
│   └── notebooks/      # Jupyter notebooks for analysis
├── frontend/           # Vue.js SPA
└── doc/                # Documentation
```

## Development Commands
- **Backend**: `docker-compose up --build -d api-gateway`
- **Frontend**: `npm install` then `npm run dev`

## Key URLs
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

## Environment Setup
- Requires Kaggle API credentials
- Requires Google OAuth 2.0 credentials
- Requires JWT secret key (generated with openssl)