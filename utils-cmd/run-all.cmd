@echo off

REM Parse arguments
set USE_LOCAL_IMAGES=false
set COMPOSE_FILE=docker-compose.yml

:parse_args
if "%1"=="" goto start_services
if "%1"=="--local-images" (
    set USE_LOCAL_IMAGES=true
    set COMPOSE_FILE=docker-compose.local.yml
    shift
    goto parse_args
)
if "%1"=="--help" (
    goto usage
)
if "%1"=="-h" (
    goto usage
)

echo Error: Invalid parameter "%1"
goto usage

:start_services
if "%USE_LOCAL_IMAGES%"=="true" (
    echo Starting services with local images...
    echo Using compose file: %COMPOSE_FILE%
) else (
    echo Starting services with Docker Hub images...
    echo Using compose file: %COMPOSE_FILE%
)

docker-compose -f %COMPOSE_FILE% up -d api-gateway frontend

if errorlevel 1 (
    echo Error: Failed to start services
    exit /b 1
)

echo Services started successfully!
echo.
echo Running services:
docker-compose -f %COMPOSE_FILE% ps api-gateway frontend
goto end

:usage
echo Usage: run-all.cmd [--local-images] [--help]
echo.
echo Options:
echo   --local-images    Use local Docker images (docker-compose.local.yml)
echo   --help, -h        Show this help message
echo.
echo Examples:
echo   run-all.cmd                     ^(uses Docker Hub images^)
echo   run-all.cmd --local-images      ^(uses local images^)
echo   run-all.cmd --help
echo.
echo Services started: api-gateway, frontend
exit /b 0

:end