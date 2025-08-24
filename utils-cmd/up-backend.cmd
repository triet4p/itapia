@echo off
echo Starting backend services...
cd backend
docker-compose up -d api-gateway
echo Backend services started successfully!