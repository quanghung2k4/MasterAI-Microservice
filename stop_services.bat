@echo off
echo Stopping Nginx...
cd /d "c:\DiskD\AndroidBE\MasterAI-Microservice\nginx"
nginx -s quit

echo.
echo Killing all Python servers...
taskkill /F /IM python.exe /T

echo.
echo All services stopped successfully!
pause