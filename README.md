# ITAPIA
### Intelligent & Transparent AI-Powered Personal Investment Assistant

![Project Status: In Development](https://img.shields.io/badge/status-in_development-yellowgreen) ![Tech Stack: Python & Vue.js](https://img.shields.io/badge/tech-Python|Vue.js|FastAPI|ScikitLearn|BERT|TALib-blue) ![License: Academic Use](https://img.shields.io/badge/license-Academic_Use-lightgrey)

ITAPIA is an intelligent stock investment assistant platform, built with the core philosophies of **transparency** and **Explainability (XAI)**. This project does not just provide recommendations, but also empowers users to understand the "why" behind each decision.

---

### The Problem & ITAPIA's Solution

*   **The Problem:** The current market is flooded with "black box" investment tools that issue cryptic buy/sell signals, eroding trust and turning investing into a game of chance.
*   **Our Solution:** We built a "glass box". By combining traditional AI/ML models with a powerful Rule Engine, every piece of advice is traced back to the "evidence" and "rules" that triggered it, giving users full control and confidence.

---

### Demo
<!-- Insert screenshot or GIF demo here -->
![ITAPIA Demo](./doc/public/itapia-demo.gif)
*(The Advisor Interface)*

---

### 📈 Key Features

*   🧠 **Hybrid AI Architecture:** Combines the strengths of traditional Machine Learning models (Forecasting), Natural Language Processing (NLP), and a symbolic Rule Engine for reasoning.
*   🔍 **Explainable Recommendations (XAI):** Every piece of advice on Decisions, Risks, and Opportunities is accompanied by a list of triggered rules as evidence.
*   🧬 **Evolvable Rule Engine:** Built on a foundation of Symbolic Expression Trees, ready for the application of genetic algorithms to automatically discover new strategies.
*   👤 **Personalized Investment Profiles:** Allows users to create and experiment with multiple investment "personas," each with unique parameters for risk appetite, goals, and experience.
*   ⚙️ **Modern Full-Stack System:** Fully built with a Backend (Python, FastAPI, Docker) and Frontend (Vue.js, TypeScript, Vuetify), delivering a smooth and professional user experience.

---

### 🏗️ Architecture Overview

ITAPIA is designed with a microservices architecture, ensuring modularity, scalability, and maintainability.

![Deployment Architecture](./doc/diagram/UML-deployment.png)

> Dive deeper into our system design in the **[Architecture Documentation](./doc/public/itapia-mvp-v1.0.md)**.

---

### 🚀 Quick Start

**Prerequisites:**
*   Git
*   Docker & Docker Compose
*   Python (Python 3.11 is recommended)
*   npm
*   OpenSSL

#### 1. Initial Setup

```bash
# Clone the repository
git clone https://github.com/your-username/itapia.git
cd itapia
```

#### 2. Environment Setup & Credentials

Before running the project, you need to prepare the following secrets:

**a. Get Kaggle API Key:**
*   Log in to [Kaggle](https://www.kaggle.com/).
*   Go to your account page (click your avatar -> Account).
*   In the "API" section, click **"Create New API Token"**.
*   A `kaggle.json` file will be downloaded. Open it; you will need the `username` and `key` values.

**b. Get Google OAuth 2.0 Credentials:**
*   Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a new project.
*   Navigate to **APIs & Services** -> **OAuth consent screen**, select **External**, and fill in the required application details. Add the `.../auth/userinfo.email` and `.../auth/userinfo.profile` scopes.
*   Go to **Credentials**, click **+ CREATE CREDENTIALS** -> **OAuth client ID**.
*   Select **Web application** and configure the following:
    *   **Authorized JavaScript origins:** `http://localhost:3000`
    *   **Authorized redirect URIs:** `http://localhost:8000/api/v1/auth/google/callback`
*   After creation, copy the **Client ID** and **Client Secret**.

**c. Generate JWT Secret Key:**
*   Open your terminal and run the following command:
    ```bash
    openssl rand -hex 32
    ```
*   Copy the generated random string.

**d. Configure `.env` files:**
Copy the configuration files from the provided templates and fill in the necessary values.
```bash
# Backend
cp ./backend/.env.template ./backend/.env

# Frontend
cp ./frontend/.env.template ./frontend/.env
```

#### 3. Run the Backend

```bash
# Navigate to the backend directory
cd backend

# Build and run all backend services in detached mode
docker-compose up --build -d api-gateway
```

#### 4. Run the Frontend

```bash
# Navigate to the frontend directory from the root
cd frontend

# Install dependencies
npm install

# Sync schemas if necessary
npm run sync:schemas

# Run the development server
npm run dev
```

#### 5. Access the System
*   **Frontend Application:** [http://localhost:3000](http://localhost:3000)
*   **Backend API Docs (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 📁 Project Structure

```
itapia/
├── backend/            # Contains all microservices, Docker config, and the .env for the backend
├── frontend/           # The Vue.js SPA, contains its own .env for the frontend
├── .gitignore
└── README.md           # You are here
```

---

### 🗺️ Development Roadmap

-   ✅ **Phase 1: Core MVP** (Analysis, Advisor, Rules, Auth)
-   ✅ **Phase 2: UI/UX Polish & Personalization** (UX Polish, Profile Management)
-   ▶️ **Phase 3: Automatic Optimization (`Evo-worker`)**
-   ▶️ **Phase 4: Deep Dive & LLM Integration**

---

### 📚 Detailed Documentation

*   **[System Architecture](./doc/public/itapia-mv-p-v1.0.md):** A deep dive into the microservices, data flow, and design decisions.
*   **[API Reference](./doc/public/API-doc-v1.pdf):** A detailed list and description of all API endpoints.
*   **[Rule Engine Architecture](./doc/public/rule-architecture.pdf):** An explanation of the Symbolic Expression Tree design.

---

### Tutorials
To understand the development process, roles, and responsibilities of each component, you can read the:
*   **[Tutorials](./doc/tutorials/index.md)**


---

### 🤝 Contributing & Citation

This is a graduate thesis project. All contributions or questions are welcome. Please create an Issue to discuss.

If you use this work, please cite it as:
```
[Le, Minh Triet]. (2025). ITAPIA: An Intelligent and Transparent AI-Powered Personal Investment Assistant. 
Graduate Thesis, Hanoi University of Science and Technology, Vietnam.
```