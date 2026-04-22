@echo off
setlocal EnableExtensions

REM ============================================================
REM Run all services (Nginx Gateway + Django microservices)
REM ============================================================

set "ROOT=%~dp0"

REM --- Default venv paths (edit if you want) ---
set "DEFAULT_VENV_ACTIVATE=D:\DjangoProject\Test-django\myenv\Scripts\activate.bat"
set "DEFAULT_VENV_PYTHON=D:\DjangoProject\Test-django\myenv\Scripts\python.exe"

REM --- Service dirs ---
set "NGINX_DIR=D:\DjangoProject\MasterAI-Microservice\nginx"
set "USER_DIR=%ROOT%user_service"
set "POST_DIR=%ROOT%post_service"
set "AI_DIR=%ROOT%ai_service"
set "NOTI_DIR=%ROOT%notification_service"
set "MESSAGE_DIR=%ROOT%message_service"

REM --- Hosts/ports ---
set "USER_HOST=0.0.0.0"
set "POST_HOST=0.0.0.0"
set "AI_HOST=0.0.0.0"
set "NOTI_HOST=0.0.0.0"


set "USER_PORT=3001"
set "POST_PORT=3002"
set "AI_PORT=3003"
set "NOTI_PORT=3004"
set "MESSAGE_PORT=3030"

REM --- Resolve venv argument ---
set "ARG=%~1"
set "VENV_ACTIVATE=%DEFAULT_VENV_ACTIVATE%"
set "VENV_PYTHON=%DEFAULT_VENV_PYTHON%"

if not "%ARG%"=="" (
  if exist "%ARG%" (
    echo %ARG% | findstr /I "python.exe" >nul
    if not errorlevel 1 (
      set "VENV_PYTHON=%ARG%"
      set "VENV_ACTIVATE="
    ) else (
      set "VENV_ACTIVATE=%ARG%"
    )
  ) else (
    echo [ERROR] Provided path does not exist:
    echo         %ARG%
    exit /b 1
  )
)

REM If activate was provided, try to derive python.exe next to it.
if defined VENV_ACTIVATE (
  for %%I in ("%VENV_ACTIVATE%") do (
    set "ACTIVATE_DIR=%%~dpI"
  )
  if exist "%ACTIVATE_DIR%python.exe" (
    set "VENV_PYTHON=%ACTIVATE_DIR%python.exe"
  )
)

REM --- Basic checks ---
REM 1. Kiểm tra xem Nginx có tồn tại không
if not exist "%NGINX_DIR%\nginx.exe" (
  echo [ERROR] Nginx không tim thay tai: %NGINX_DIR%\nginx.exe
  exit /b 1
)
REM 2. Kiểm tra các microservices
if not exist "%USER_DIR%\manage.py" (
  echo [ERROR] Not found: %USER_DIR%\manage.py
  exit /b 1
)
if not exist "%POST_DIR%\manage.py" (
  echo [ERROR] Not found: %POST_DIR%\manage.py
  exit /b 1
)
if not exist "%AI_DIR%\manage.py" (
  echo [ERROR] Not found: %AI_DIR%\manage.py
  exit /b 1
)
if not exist "%NOTI_DIR%\manage.py" (
  echo [ERROR] Not found: %NOTI_DIR%\manage.py
  exit /b 1
)

echo.
echo Starting services...
if not exist "%VENV_PYTHON%" (
  echo [ERROR] Python exe not found:
  echo         %VENV_PYTHON%
  echo.
  echo Provide python.exe directly, e.g.:
  echo   run_all_services.bat "D:\DjangoProject\Test-django\myenv\Scripts\python.exe"
  exit /b 1
)

echo Using venv python:
echo   %VENV_PYTHON%
if defined VENV_ACTIVATE (
  echo (activate provided: %VENV_ACTIVATE%)
)

echo.
echo Ports:
echo   Nginx Gateway : Port 8000
echo   User Service  : %USER_HOST%:%USER_PORT%
echo   Post Service  : %POST_HOST%:%POST_PORT%
echo   Ai Service    : %AI_HOST%:%AI_PORT%
echo   Noti Service    : %NOTI_HOST%:%NOTI_POST%
echo.

echo Starting Services with NGINX...
echo.

REM --- Start Nginx Gateway ---
echo Starting Nginx on port 8000...
start "Nginx Gateway" /d "%NGINX_DIR%" nginx.exe

REM --- Start each service in its own window ---
start "User Service" powershell -NoExit -ExecutionPolicy Bypass -Command "Set-Location -LiteralPath '%USER_DIR%'; & '%VENV_PYTHON%' manage.py runserver %USER_HOST%:%USER_PORT%"
start "Post Service" powershell -NoExit -ExecutionPolicy Bypass -Command "Set-Location -LiteralPath '%POST_DIR%'; & '%VENV_PYTHON%' manage.py runserver %POST_HOST%:%POST_PORT%"
start "AI Service" powershell -NoExit -ExecutionPolicy Bypass -Command "Set-Location -LiteralPath '%AI_DIR%'; & '%VENV_PYTHON%' manage.py runserver %AI_HOST%:%AI_PORT%"
start "Notification Service" powershell -NoExit -ExecutionPolicy Bypass -Command "Set-Location -LiteralPath '%NOTI_DIR%'; & '%VENV_PYTHON%' manage.py runserver %NOTI_HOST%:%NOTI_PORT%"
start "Message Service" powershell -NoExit -ExecutionPolicy Bypass -Command "Set-Location -LiteralPath '%MESSAGE_DIR%'; & '%VENV_PYTHON%' manage.py runserver 0.0.0.0:%MESSAGE_PORT%"

echo Done. 
echo [WARNING] Closing this window does NOT stop Nginx.
echo To stop Nginx, you must run: cd /d "%NGINX_DIR%" ^& nginx -s quit
echo.
pause
endlocal