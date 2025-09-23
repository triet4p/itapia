@echo off

REM Parse --local-tag and --hub-tag
set LOCAL_TAG=latest
set HUB_TAG=latest
set DOCKER_USER=trietlm2004

:parse_args
if "%1"=="" goto start_push
if "%1"=="--local-tag" (
    if "%2"=="" (
        echo Error: --local-tag requires a value
        goto usage
    )
    set LOCAL_TAG=%2
    shift
    shift
    goto parse_args
)
if "%1"=="--hub-tag" (
    if "%2"=="" (
        echo Error: --hub-tag requires a value
        goto usage
    )
    set HUB_TAG=%2
    shift
    shift
    goto parse_args
)
if "%1"=="--user" (
    if "%2"=="" (
        echo Error: --user requires a value
        goto usage
    )
    set DOCKER_USER=%2
    shift
    shift
    goto parse_args
)

echo Error: Invalid parameter "%1"
goto usage

:usage
echo Usage: push-docker-hub.cmd [--local-tag ^<tag^>] [--hub-tag ^<tag^>] [--user ^<username^>]
echo.
echo Options:
echo   --local-tag    Local Docker image tag (default: latest)
echo   --hub-tag      Docker Hub image tag (default: latest)  
echo   --user         Docker Hub username (default: trietlm2004)
echo.
echo Examples:
echo   push-docker-hub.cmd
echo   push-docker-hub.cmd --local-tag v1.0.0 --hub-tag v1.0.0
echo   push-docker-hub.cmd --local-tag latest --hub-tag stable
echo   push-docker-hub.cmd --user myuser --hub-tag v2.0.0
exit /b 1

:start_push
echo Pushing all docker images to Docker Hub...
echo Local tag: %LOCAL_TAG%
echo Hub tag: %HUB_TAG%
echo Docker user: %DOCKER_USER%
echo.

REM Define array of image names
set IMAGES=itapia-data-processor itapia-data-seeds itapia-api-gateway itapia-ai-service-quick itapia-evo-worker itapia-frontend

REM Process each image
for %%i in (%IMAGES%) do (
    echo Processing %%i...
    docker tag %%i:%LOCAL_TAG% %DOCKER_USER%/%%i:%HUB_TAG%
    if errorlevel 1 (
        echo Error: Failed to tag %%i
        exit /b 1
    )
    
    docker push %DOCKER_USER%/%%i:%HUB_TAG%
    if errorlevel 1 (
        echo Error: Failed to push %%i
        exit /b 1
    )
    echo %%i pushed successfully!
    echo.
)

echo All images pushed successfully!