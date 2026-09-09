@echo off
title IoT Irrigation - Blynk Bridge
color 0A

echo.
echo ========================================
echo   IoT Irrigation Blynk Bridge Launcher
echo ========================================
echo.

:: Check .env exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please copy .env.example to .env and fill in your Blynk token.
    pause
    exit /b 1
)

:: Check token is set
findstr /C:"YOUR_DEVICE_AUTH_TOKEN_HERE" .env >nul 2>&1
if %errorlevel%==0 (
    echo ERROR: You must set your real Blynk token in .env
    echo.
    echo Open .env and replace:
    echo   BLYNK_AUTH_TOKEN=YOUR_DEVICE_AUTH_TOKEN_HERE
    echo with your real token from blynk.cloud
    echo.
    notepad .env
    pause
    exit /b 1
)

:: Check COM ports
echo Checking COM ports...
python -c "import serial; ports=[p.device for p in __import__('serial.tools.list_ports',fromlist=['comports']).comports()]; print('Available:',ports)"

echo.
echo Starting Blynk bridge...
echo Press Ctrl+C to stop.
echo.

python blynk_bridge.py

pause
