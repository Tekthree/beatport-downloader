"""
Test script to verify Beatport Auto Downloader functionality
"""
import os
import sys
import logging
from beatport_auto.main import BeatportTrackFinder
from beatport_auto.utils.selector_manager import SelectorsManager

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('test_output.txt')
        ]
    )

def test_selectors():
    """Test the SelectorsManager with both layouts"""
    logging.info("Testing SelectorsManager functionality...")
    
    # Initialize SelectorsManager
    selector_manager = SelectorsManager()
    
    # Verify selectors are loaded
    if not selector_manager.selectors:
        logging.error("Failed to load selectors")
        return False
        
    logging.info("Successfully loaded selectors")
    return True

def test_track_finder():
    """Test the BeatportTrackFinder core functionality"""
    logging.info("Testing BeatportTrackFinder...")
    
    try:
        finder = BeatportTrackFinder(headless=False)
        logging.info("Successfully initialized BeatportTrackFinder")
        return True
    except Exception as e:
        logging.error(f"Error initializing BeatportTrackFinder: {e}")
        return False

def main():
    setup_logging()
    logging.info("Starting application test...")
    
    # Test components
    if not test_selectors():
        logging.error("Selector test failed")
        return
        
    if not test_track_finder():
        logging.error("Track finder test failed")
        return
    
    logging.info("All tests completed successfully!")
    logging.info("You can now run the main application")

if __name__ == "__main__":
    main()
