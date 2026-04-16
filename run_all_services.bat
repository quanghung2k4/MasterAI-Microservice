@echo off
setlocal EnableExtensions

REM ============================================================
REM Run all Django services (API Gateway + microservices)
REM Usage:
REM   run_all_services.bat
REM   run_all_services.bat "D:\path\to\venv\Scripts\activate.bat"
REM   run_all_services.bat "D:\path\to\venv\Scripts\python.exe"
REM ============================================================

set "ROOT=%~dp0"

REM --- Default venv paths (edit if you want) ---
set "DEFAULT_VENV_ACTIVATE=C:\DiskD\AndroidBackend\MasterAI-Microservice\venv\Scripts\activate.bat"
set "DEFAULT_VENV_PYTHON=C:\DiskD\AndroidBackend\MasterAI-Microservice\venv\Scripts\python.exe"

REM --- Service dirs ---
set "GATEWAY_DIR=%ROOT%api_gateway"
set "USER_DIR=%ROOT%user_service"
set "POST_DIR=%ROOT%post_service"

REM --- Hosts/ports ---
set "GATEWAY_HOST=0.0.0.0"
set "USER_HOST=0.0.0.0"
set "POST_HOST=0.0.0.0"

set "GATEWAY_PORT=8000"
set "USER_PORT=3001"
set "POST_PORT=3002"

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
if not exist "%GATEWAY_DIR%\manage.py" (
  echo [ERROR] Not found: %GATEWAY_DIR%\manage.py
  exit /b 1
)
if not exist "%USER_DIR%\manage.py" (
  echo [ERROR] Not found: %USER_DIR%\manage.py
  exit /b 1
)
if not exist "%POST_DIR%\manage.py" (
  echo [ERROR] Not found: %POST_DIR%\manage.py
  exit /b 1
)

echo.
echo Starting services...
if not exist "%VENV_PYTHON%" (
  echo [ERROR] Python exe not found:
  echo         %VENV_PYTHON%
  echo.
  echo Provide python.exe directly, e.g.:
  echo   run_all_services.bat "C:\DiskD\AndroidBackend\MasterAI-Microservice\venv\Scripts\python.exe"
  exit /b 1
)

echo Using venv python:
echo   %VENV_PYTHON%
if defined VENV_ACTIVATE (
  echo (activate provided: %VENV_ACTIVATE%)
)

echo.
echo Ports:
echo   API Gateway : %GATEWAY_HOST%:%GATEWAY_PORT%
echo   User Service: %USER_HOST%:%USER_PORT%
echo   Post Service: %POST_HOST%:%POST_PORT%
echo.

REM --- Start each service in its own window (PowerShell is robust under Windows Terminal default shell) ---
start "API Gateway" powershell -NoExit -ExecutionPolicy Bypass -Command "Set-Location -LiteralPath '%GATEWAY_DIR%'; & '%VENV_PYTHON%' manage.py runserver %GATEWAY_HOST%:%GATEWAY_PORT%"
start "User Service" powershell -NoExit -ExecutionPolicy Bypass -Command "Set-Location -LiteralPath '%USER_DIR%'; & '%VENV_PYTHON%' manage.py runserver %USER_HOST%:%USER_PORT%"
start "Post Service" powershell -NoExit -ExecutionPolicy Bypass -Command "Set-Location -LiteralPath '%POST_DIR%'; & '%VENV_PYTHON%' manage.py runserver %POST_HOST%:%POST_PORT%"

echo Done. Close the opened PowerShell windows to stop services.
echo.
endlocal
