docker build -t itapia-data-processor:latest -f data_processing/Dockerfile .
docker build -t itapia-api-gateway:latest -f api_gateway/Dockerfile .
docker build -t itapia-ai-service-quick:latest -f ai_service_quick/Dockerfile .
docker system prune -f