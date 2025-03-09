"""
Build script for creating a professional Gumroad-ready Beatport Auto Downloader
"""
import os
import sys
import shutil
from pathlib import Path

def clean_dist():
    """Clean previous build artifacts"""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    print("Cleaned previous build files")

def build_executable():
    """Build the Windows executable"""
    import PyInstaller.__main__
    
    PyInstaller.__main__.run([
        'beatport_auto/main.py',
        '--name=Beatport Auto Downloader',
        '--onefile',
        '--noconsole',
        '--icon=app_icon.ico',
        '--add-data=beatport_auto/data/selectors.json:beatport_auto/data',
        '--hidden-import=selenium',
        '--hidden-import=webdriver_manager',
        '--windowed',
    ])

def create_distribution():
    """Create final distribution package"""
    dist_dir = Path('dist')
    package_dir = dist_dir / 'Beatport Auto Downloader Package'
    package_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy executable
    shutil.copy2(
        dist_dir / 'Beatport Auto Downloader.exe',
        package_dir / 'Beatport Auto Downloader.exe'
    )
    
    # Copy documentation
    shutil.copy2('GUMROAD_README.md', package_dir / 'README.md')
    
    # Create quick start guide
    with open(package_dir / 'Quick Start Guide.txt', 'w') as f:
        f.write("""Beatport Auto Downloader
======================

Quick Start Guide:
1. Double-click 'Beatport Auto Downloader.exe'
2. Log in to your Beatport account when prompted
3. Your tracks will automatically download to your chosen location

Need help? Contact support at: [Your Support Email]

Updates:
- Check Gumroad for the latest version
- Download and replace the .exe file to update

Thank you for your purchase!""")

    # Create a ZIP file for Gumroad
    shutil.make_archive(
        dist_dir / 'Beatport Auto Downloader',
        'zip',
        package_dir
    )

if __name__ == '__main__':
    print("Building Beatport Auto Downloader...")
    clean_dist()
    build_executable()
    create_distribution()
    print("\nBuild complete! Your Gumroad-ready package is in:")
    print("- ZIP file: dist/Beatport Auto Downloader.zip")
    print("- Unzipped: dist/Beatport Auto Downloader Package")
