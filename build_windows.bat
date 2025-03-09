@echo off
echo Building Beatport Auto Downloader...

REM Install required packages if not already installed
pip install pyinstaller

REM Clean previous builds
rmdir /s /q build dist
del /q *.spec

REM Create the executable
pyinstaller --name="Beatport Auto Downloader" ^
    --onefile ^
    --noconsole ^
    --icon=app_icon.ico ^
    --add-data="beatport_auto/data/selectors.json;beatport_auto/data" ^
    --hidden-import=selenium ^
    --hidden-import=webdriver_manager ^
    --windowed ^
    beatport_auto/main.py

REM Create distribution package
mkdir "dist\Beatport Auto Downloader Package"
copy "dist\Beatport Auto Downloader.exe" "dist\Beatport Auto Downloader Package\"
copy "GUMROAD_README.md" "dist\Beatport Auto Downloader Package\README.md"

REM Create Quick Start Guide
echo Beatport Auto Downloader > "dist\Beatport Auto Downloader Package\Quick Start Guide.txt"
echo ====================== >> "dist\Beatport Auto Downloader Package\Quick Start Guide.txt"
echo. >> "dist\Beatport Auto Downloader Package\Quick Start Guide.txt"
echo Quick Start Guide: >> "dist\Beatport Auto Downloader Package\Quick Start Guide.txt"
echo 1. Double-click 'Beatport Auto Downloader.exe' >> "dist\Beatport Auto Downloader Package\Quick Start Guide.txt"
echo 2. Log in to your Beatport account when prompted >> "dist\Beatport Auto Downloader Package\Quick Start Guide.txt"
echo 3. Your tracks will automatically download to your chosen location >> "dist\Beatport Auto Downloader Package\Quick Start Guide.txt"
echo. >> "dist\Beatport Auto Downloader Package\Quick Start Guide.txt"
echo Need help? Contact support at: [Your Support Email] >> "dist\Beatport Auto Downloader Package\Quick Start Guide.txt"
echo. >> "dist\Beatport Auto Downloader Package\Quick Start Guide.txt"
echo Updates: >> "dist\Beatport Auto Downloader Package\Quick Start Guide.txt"
echo - Check Gumroad for the latest version >> "dist\Beatport Auto Downloader Package\Quick Start Guide.txt"
echo - Download and replace the .exe file to update >> "dist\Beatport Auto Downloader Package\Quick Start Guide.txt"
echo. >> "dist\Beatport Auto Downloader Package\Quick Start Guide.txt"
echo Thank you for your purchase! >> "dist\Beatport Auto Downloader Package\Quick Start Guide.txt"

REM Create ZIP file
powershell Compress-Archive -Path "dist\Beatport Auto Downloader Package\*" -DestinationPath "dist\Beatport Auto Downloader.zip" -Force

echo.
echo Build complete! Your Gumroad-ready package is in:
echo - ZIP file: dist\Beatport Auto Downloader.zip
echo - Unzipped: dist\Beatport Auto Downloader Package
pause
