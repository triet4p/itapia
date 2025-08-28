@echo off
echo Starting DB services...
cd backend
docker-compose up -d stocks_postgre_db realtime_redis_db
echo DB services started successfully!