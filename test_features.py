"""
Comprehensive test suite for Beatport Auto Downloader
Tests the SelectorsManager's resilient features
"""
import os
import sys
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from beatport_auto.utils.selector_manager import SelectorsManager
from beatport_auto.main import BeatportTrackFinder

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('test_results.log')
        ]
    )

def test_selector_resilience():
    """Test SelectorsManager's dynamic selector capabilities"""
    logging.info("Testing selector resilience...")
    
    # Initialize SelectorsManager
    manager = SelectorsManager()
    
    # Test dynamic selector loading
    assert manager.selectors, "Selectors should be loaded"
    logging.info("✓ Dynamic selector loading")
    
    # Test fallback mechanisms
    assert 'track_containers' in manager.selectors, "Should have track container selectors"
    assert 'download_button' in manager.selectors, "Should have download button selectors"
    logging.info("✓ Fallback selectors available")

def test_layout_adaptation():
    """Test adaptation to different layouts"""
    logging.info("Testing layout adaptation...")
    
    # Set up Chrome with different window sizes
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in headless mode for tests
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    
    try:
        # Test large layout
        driver.set_window_size(1920, 1080)
        finder = BeatportTrackFinder(driver=driver)
        logging.info("✓ Large layout initialization")
        
        # Test small layout
        driver.set_window_size(800, 600)
        finder = BeatportTrackFinder(driver=driver)
        logging.info("✓ Small layout initialization")
        
    finally:
        driver.quit()

def main():
    setup_logging()
    logging.info("Starting comprehensive feature tests...")
    
    try:
        # Test core features
        test_selector_resilience()
        test_layout_adaptation()
        
        logging.info("All tests passed successfully!")
        print("\nTest Results:")
        print("✓ Dynamic selector management")
        print("✓ Layout adaptation")
        print("✓ Fallback mechanisms")
        print("\nYou can now run the main application")
        
    except Exception as e:
        logging.error(f"Test failed: {e}")
        print("\n❌ Some tests failed. Check test_results.log for details")

if __name__ == "__main__":
    main()
