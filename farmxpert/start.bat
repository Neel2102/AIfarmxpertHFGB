@echo off
setlocal enableextensions enabledelayedexpansion

REM Project root directory (repo root, parent of this farmxpert folder)
set ROOT=%~dp0..
pushd "%ROOT%"

echo.
echo ===== FarmXpert Starter =====
echo Creating/activating Python venv and installing backend deps...

REM Create venv if missing
if not exist .venv (
  python -m venv .venv
)

REM Upgrade pip and install backend requirements
call .\.venv\Scripts\python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :error
call .\.venv\Scripts\pip install -r farmxpert\requirements.txt
if errorlevel 1 goto :error

echo.
echo Checking Node.js and installing frontend deps...
if not exist farmxpert\frontend\package.json (
  echo Frontend directory not found. Skipping frontend start.
  goto :start_backend_only
)

REM Install frontend deps using npm ci when lockfile exists
pushd farmxpert\frontend
if exist package-lock.json (
  call npm ci --no-audit --no-fund
) else (
  call npm install --no-audit --no-fund
)
if errorlevel 1 (
  echo Failed to install frontend dependencies. Continuing to start servers...
)
popd

REM Start backend in new terminal
:start_servers
echo.
echo Starting backend (port 8000) and frontend (port 3000) in separate windows...

REM Backend window
start "FarmXpert Backend" cmd /k "cd /d "%ROOT%" && .\.venv\Scripts\python -m uvicorn farmxpert.interfaces.api.main:app --reload --host 0.0.0.0 --port 8000 --app-dir "%ROOT%""

REM Frontend window
start "FarmXpert Frontend" cmd /k "cd /d "%ROOT%\farmxpert\frontend" && npm start"

echo.
echo Servers launching. Backend: http://localhost:8000  Frontend: http://localhost:3000
echo Press any key to exit this launcher...
pause >nul
goto :eof

:start_backend_only
echo Starting only backend as frontend is missing...
start "FarmXpert Backend" cmd /k "cd /d "%ROOT%" && .\.venv\Scripts\python -m uvicorn farmxpert.interfaces.api.main:app --reload --host 0.0.0.0 --port 8000 --app-dir "%ROOT%""
echo Backend launching at http://localhost:8000
echo Press any key to exit this launcher...
pause >nul
goto :eof

:error
echo.
echo There was an error during setup. See logs above.
echo Press any key to exit...
pause >nul
exit /b 1


