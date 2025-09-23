# ITAPIA Backend Tutorials

Here are the tutorials that explain how we build the ITAPIA Backend. Each service has its own specific role in our microservices architecture.

## Services Overview

### [Shared Library](./shared/index.md)
The central nervous system of our financial analysis application. It structures all financial data, manages database connections, and implements a powerful rule engine that uses customizable logic trees to evaluate analysis reports and translate insights into actionable trading advice.

### [Data Processing](./data_processing/index.md)
Responsible for automatically collecting, processing, and storing various types of financial data. It fetches information like daily and real-time stock prices from Yahoo Finance and news articles from Google News, then cleans, transforms, and standardizes the data before storing it in databases or caching layers.

### [Data Seeds](./data_seeds/index.md)
Handles initializing databases with all necessary starting information. It sets up database structure by creating tables and populates them with default data in a specific order that preserves data integrity. It also ensures predefined operational rules are loaded for proper application functionality.

### [Evo Worker](./evo_worker/index.md)
A sophisticated system for automatic discovery and optimization of trading strategies. It uses evolutionary algorithms to iteratively generate, evaluate, and refine potential trading rules, aiming to find strategies that are both profitable and robust through genetic operations and performance measurement.

### [AI Service Quick](./ai_service_quick/index.md)
Functions as a comprehensive financial intelligence platform. It generates detailed market analysis reports by combining technical, forecasting, and news data, then leverages personalized trading rules and user preferences to deliver actionable investment recommendations with clear explanations.

### [API Gateway](./api_gateway/index.md)
Acts as the central hub for various financial services. It organizes access to AI-powered analytics, advisor tools, and market data viewers while managing user accounts and investment profiles. It also securely handles user authentication and ensures proper routing and configuration for all requests.