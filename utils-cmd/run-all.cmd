@echo off
echo Starting all services...

echo Starting backend API gateway...
cd backend
docker-compose up -d api-gateway
cd ..

echo Starting frontend development server...
cd frontend
npm run dev