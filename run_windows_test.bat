@echo off
echo Beatport Auto Downloader Test Suite
echo =================================

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Run feature tests
echo.
echo Running feature tests...
python test_features.py

REM Test main application
echo.
echo Would you like to test the main application? (Y/N)
set /p choice=
if /i "%choice%"=="Y" (
    echo.
    echo Starting Beatport Auto Downloader...
    echo - Log in when prompted
    echo - Test downloading tracks
    echo - Try different window sizes
    echo.
    python beatport_auto/main.py
)

pause
