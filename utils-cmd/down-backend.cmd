@echo off
echo Terminating backend services...
cd backend
docker-compose down
echo Backend services end successfully!