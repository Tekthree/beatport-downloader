@echo off
echo Testing Beatport Auto Downloader locally...

REM Install dependencies in development mode
python -m pip install -e .

REM Run the selector tests first
echo.
echo Testing selectors...
python test_selectors.py --downloads

REM Run the main application
echo.
echo Starting main application...
python beatport_auto/main.py

pause
