@echo off
setlocal enableextensions enabledelayedexpansion

REM Project root directory (repo root)
set ROOT=%~dp0
pushd "%ROOT%"

echo.
echo ===== FarmXpert Docker Launcher =====
echo Checking for Docker...

docker --version >nul 2>&1
if errorlevel 1 (
    echo Docker is not installed or not running in the PATH.
    echo Please start Docker Desktop and ensure it is running.
    echo.
    pause
    goto :eof
)

echo Making sure the SQLite database file exists so Docker maps it correctly as a file...
if not exist "backend\farmxpert.db" (
    type nul > "backend\farmxpert.db"
)

echo.
echo Starting Docker containers (Enterprise Postgres + PGbouncer + Backend + Frontend)...
cd backend\farmxpert
docker compose down
docker compose up -d --build

if errorlevel 1 (
    echo.
    echo There was an error starting the Docker containers.
    pause
    goto :eof
)

echo.
echo Servers are launching in Docker!
echo Backend API : http://localhost:8000
echo Frontend UI : http://localhost:3000
echo.
echo ----------------------------------------------------
echo To stop servers, run in your terminal: docker compose down
echo To view live logs, run: docker compose logs -f
echo ----------------------------------------------------
echo.
pause
goto :eof
