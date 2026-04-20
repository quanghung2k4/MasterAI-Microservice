@echo off
echo Stopping Nginx...
cd /d "D:\DjangoProject\MasterAI-Microservice\nginx"
nginx -s quit

echo.
echo Killing all Python servers...
taskkill /F /IM python.exe /T

echo.
echo All services stopped successfully!
pause