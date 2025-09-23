# ITAPIA Tutorials

Here are the tutorials that explain how we build ITAPIA, covering both backend and frontend components.

## Architecture Overview

ITAPIA is built using a microservices architecture with a Vue 3 frontend and multiple backend services that work together to provide an AI-powered investment platform.

## [Backend Tutorials](./backend/index.md)

The backend consists of multiple specialized microservices:

### [Shared Library](./backend/shared/index.md)
The central nervous system of our financial analysis application. It structures all financial data, manages database connections, and implements a powerful rule engine that uses customizable logic trees to evaluate analysis reports and translate insights into actionable trading advice.

### [Data Processing](./backend/data_processing/index.md)
Responsible for automatically collecting, processing, and storing various types of financial data. It fetches information like daily and real-time stock prices from Yahoo Finance and news articles from Google News, then cleans, transforms, and standardizes the data before storing it in databases or caching layers.

### [Data Seeds](./backend/data_seeds/index.md)
Handles initializing databases with all necessary starting information. It sets up database structure by creating tables and populates them with default data in a specific order that preserves data integrity. It also ensures predefined operational rules are loaded for proper application functionality.

### [Evo Worker](./backend/evo_worker/index.md)
A sophisticated system for automatic discovery and optimization of trading strategies. It uses evolutionary algorithms to iteratively generate, evaluate, and refine potential trading rules, aiming to find strategies that are both profitable and robust through genetic operations and performance measurement.

### [AI Service Quick](./backend/ai_service_quick/index.md)
Functions as a comprehensive financial intelligence platform. It generates detailed market analysis reports by combining technical, forecasting, and news data, then leverages personalized trading rules and user preferences to deliver actionable investment recommendations with clear explanations.

### [API Gateway](./backend/api_gateway/index.md)
Acts as the central hub for various financial services. It organizes access to AI-powered analytics, advisor tools, and market data viewers while managing user accounts and investment profiles. It also securely handles user authentication and ensures proper routing and configuration for all requests.

## [Frontend Tutorials](./frontend/index.md)

The frontend is a sophisticated Vue 3 application with Vuetify:

### [Vue Application Core](./frontend/03_vue_application_core_.md)
The foundation of the frontend application built with Vue 3, which initializes state management, configures routing, and renders the UI using the Vuetify framework.

### [UI Framework (Vuetify)](./frontend/02_ui_framework__vuetify__.md)
The UI component framework that provides a consistent and responsive design system for the application.

### [Routing & Navigation](./frontend/01_routing___navigation_.md)
Handles application routing and navigation between different views and components.

### [User Authentication](./frontend/04_user_authentication_.md)
Manages user login, authentication tokens, and protected routes to ensure a secure experience.

### [API Communication](./frontend/05_api_communication__axios___openapi_types__.md)
Handles communication with backend services using Axios and strongly-typed OpenAPI definitions.

### [State Management (Pinia Stores)](./frontend/06_state_management__pinia_stores__.md)
Manages application state using Pinia stores for user data, investment profiles, and AI analysis results.

### [Investment Profiles](./frontend/07_investment_profiles_.md)
Allows users to create and manage personalized investment profiles that configure their AI advisor preferences.

### [AI Investment Advisor](./frontend/08_ai_investment_advisor_.md)
Presents AI-generated investment recommendations based on user profiles and market analysis.

### [AI Market Analysis](./frontend/09_ai_market_analysis_.md)
Displays comprehensive AI-powered market analysis reports for specific stocks.

### [Trading Rules & Nodes](./frontend/10_trading_rules___nodes_.md)
Visualizes the underlying trading rules and logic that drive AI investment decisions.

### [Automated Imports & Components](./frontend/11_automated_imports___components_.md)
Supports development through automated component imports and code generation.