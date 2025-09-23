@echo off

REM Check --tag argument
set TAG=latest
set INPUT_TAG=%1

REM Parse --tag argument
if "%INPUT_TAG%"=="--tag" (
    if "%2"=="" (
        echo Error: --tag requires a value
        goto usage
    )
    set TAG=%2
) else if "%INPUT_TAG%"=="--help" (
    goto usage
) else if "%INPUT_TAG%"=="-h" (
    goto usage
) else if not "%INPUT_TAG%"=="" (
    echo Error: Invalid parameter "%INPUT_TAG%"
    goto usage
)

echo Rebuilding all Docker images with tag: %TAG%
docker-compose down

echo Build backend images
cd backend
docker build -t itapia-data-processor:%TAG% -f data_processing/Dockerfile .
if errorlevel 1 (
    echo Error: Failed to build itapia-data-processor
    exit /b 1
)

docker build -t itapia-data-seeds:%TAG% -f data_seeds/Dockerfile .
if errorlevel 1 (
    echo Error: Failed to build itapia-data-seeds
    exit /b 1
)

docker build -t itapia-api-gateway:%TAG% -f api_gateway/Dockerfile .
if errorlevel 1 (
    echo Error: Failed to build itapia-api-gateway
    exit /b 1
)

docker build -t itapia-ai-service-quick:%TAG% -f ai_service_quick/Dockerfile .
if errorlevel 1 (
    echo Error: Failed to build itapia-ai-service-quick
    exit /b 1
)

docker build -t itapia-evo-worker:%TAG% -f evo_worker/Dockerfile .
if errorlevel 1 (
    echo Error: Failed to build itapia-evo-worker
    exit /b 1
)

cd ..

echo Build frontend images
cd frontend
docker build -t itapia-frontend:%TAG% -f Dockerfile .
if errorlevel 1 (
    echo Error: Failed to build itapia-frontend
    exit /b 1
)

cd ..
docker system prune -f
echo All images rebuilt successfully with tag: %TAG%!
goto end

:usage
echo Usage: rebuild-all.cmd [--tag ^<tag_name^>] [--help]
echo.
echo Options:
echo   --tag ^<tag_name^>    Docker image tag (default: latest)
echo   --help, -h          Show this help message
echo.
echo Examples:
echo   rebuild-all.cmd                    ^(uses default tag: latest^)
echo   rebuild-all.cmd --tag latest
echo   rebuild-all.cmd --tag v1.0.0
echo   rebuild-all.cmd --tag stable
echo   rebuild-all.cmd --help
exit /b 0

:end