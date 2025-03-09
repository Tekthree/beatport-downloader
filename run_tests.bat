@echo off
echo Running Beatport Auto Downloader Tests
echo ====================================

REM Set up Python environment
echo Setting up test environment...
python -m pip install -e .

REM Test SelectorsManager
echo.
echo Testing SelectorsManager...
python beatport_auto/utils/selector_manager.py

REM Test main application
echo.
echo Testing main application...
echo This will open Chrome and navigate to Beatport
echo Please log in when prompted
echo.
echo Testing features:
echo 1. Smart track detection
echo 2. Layout adaptation
echo 3. Error recovery
echo 4. Automatic downloads
echo.
python beatport_auto/main.py

pause
