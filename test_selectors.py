import os
import time
import json
import logging
import traceback
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

# Import the SelectorsManager from main.py
import sys
sys.path.append(str(Path(__file__).parent))
from main import SelectorsManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("selector_test.log")
    ]
)

class SelectorTester:
    def __init__(self, test_downloads_page=False):
        self.test_downloads_page = test_downloads_page
        self.driver = None
        self.wait = None
        self.selector_manager = SelectorsManager()
        self.test_results = {}
        
    def initialize_browser(self):
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
        })
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        logging.info("Browser initialized successfully")
        
    def handle_login(self):
        """Navigate to login page and wait for user to login manually"""
        try:
            # Navigate to login page
            self.driver.get("https://www.beatport.com/account/login")
            logging.info("Please log in to Beatport manually. The test will continue after login...")
            
            # Wait until URL changes (indicating login success)
            try:
                WebDriverWait(self.driver, 120).until(
                    lambda driver: "account/login" not in driver.current_url
                )
                logging.info("Login detected, continuing with tests...")
                return True
            except TimeoutException:
                logging.error("Login timeout expired. Test cannot continue without login.")
                return False
                
        except Exception as e:
            logging.error(f"Error during login process: {e}")
            return False
            
    def navigate_to_test_page(self):
        """Navigate to the appropriate page for testing selectors"""
        try:
            if self.test_downloads_page:
                self.driver.get("https://www.beatport.com/library/downloads")
                logging.info("Navigated to Downloads page for testing")
            else:
                self.driver.get("https://www.beatport.com/library")
                logging.info("Navigated to Library page for testing")
                
            # Wait for page to load properly
            time.sleep(3)
            return True
            
        except Exception as e:
            logging.error(f"Error navigating to test page: {e}")
            return False
    
    def test_selector(self, selector_type, context_element=None, multiple=True):
        """Test a specific selector type and record results"""
        try:
            elements = self.selector_manager.find_element_with_learning(
                self.driver, 
                selector_type, 
                context_element=context_element, 
                wait=self.wait,
                multiple=multiple
            )
            
            success = elements is not None and (len(elements) > 0 if multiple else True)
            count = len(elements) if multiple and elements else 1 if elements else 0
            
            # Record which selector actually worked
            working_selector = None
            if success:
                selector_stats = self.selector_manager.selector_stats.get(selector_type, {})
                for selector, stats in selector_stats.items():
                    if stats['hits'] > 0:
                        working_selector = selector
                        break
            
            result = {
                "success": success,
                "count": count,
                "working_selector": working_selector,
                "error": None
            }
            
            if success:
                logging.info(f"✓ {selector_type}: Found {count} element(s) with selector: {working_selector}")
            else:
                logging.warning(f"✗ {selector_type}: Failed to find elements")
                
            return result
            
        except Exception as e:
            logging.error(f"Error testing {selector_type}: {e}")
            error_msg = str(e)
            return {
                "success": False,
                "count": 0,
                "working_selector": None,
                "error": error_msg
            }
    
    def run_tests(self):
        """Run tests for all selectors"""
        try:
            self.initialize_browser()
            
            # Handle login process
            if not self.handle_login():
                logging.error("Login failed, cannot continue tests")
                return False
                
            # Navigate to appropriate test page
            if not self.navigate_to_test_page():
                logging.error("Navigation failed, cannot continue tests")
                return False
                
            # Test track containers selector
            self.test_results["track_containers"] = self.test_selector("track_containers")
            
            # If we found track containers, test other selectors within them
            if self.test_results["track_containers"]["success"]:
                track_containers = self.selector_manager.find_element_with_learning(
                    self.driver, "track_containers", wait=self.wait
                )
                
                if track_containers and len(track_containers) > 0:
                    # Test on first container
                    sample_container = track_containers[0]
                    self.test_results["track_name"] = self.test_selector(
                        "track_name", context_element=sample_container, multiple=False
                    )
                    self.test_results["artist_name"] = self.test_selector(
                        "artist_name", context_element=sample_container
                    )
                    self.test_results["download_button"] = self.test_selector(
                        "download_button", context_element=sample_container
                    )
            
            # Test pagination selectors
            self.test_results["next_button"] = self.test_selector("next_button")
            
            # Save results
            self.save_results()
            
            return True
            
        except Exception as e:
            logging.error(f"Error running tests: {e}")
            traceback.print_exc()
            return False
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_results(self):
        """Save test results to files"""
        try:
            # Save detailed JSON results
            results_path = Path(__file__).parent / "selector_test_results.json"
            with open(results_path, 'w') as f:
                json.dump(self.test_results, f, indent=2)
                
            # Generate human-readable summary
            summary_path = Path(__file__).parent / "selector_test_summary.txt"
            
            successful = 0
            failed = 0
            
            with open(summary_path, 'w') as f:
                f.write("=== Beatport Selector Test Summary ===\n\n")
                
                for selector_type, results in self.test_results.items():
                    if results["success"]:
                        successful += 1
                        status = "✓ SUCCESS"
                    else:
                        failed += 1
                        status = "✗ FAILED"
                        
                    f.write(f"{status} - {selector_type}:\n")
                    f.write(f"  Found: {results['count']} element(s)\n")
                    
                    if results["working_selector"]:
                        f.write(f"  Working selector: {results['working_selector']}\n")
                    
                    if results["error"]:
                        f.write(f"  Error: {results['error']}\n")
                        
                    f.write("\n")
                    
                # Write summary stats
                total = successful + failed
                f.write(f"=== Summary Statistics ===\n")
                f.write(f"Total selectors tested: {total}\n")
                f.write(f"Successful: {successful} ({successful/total*100:.1f}%)\n")
                f.write(f"Failed: {failed} ({failed/total*100:.1f}%)\n")
                
            logging.info(f"Results saved to {results_path} and {summary_path}")
            
            # Print summary to console
            print("\n=== Selector Test Summary ===")
            print(f"Total selectors tested: {total}")
            print(f"Successful: {successful} ({successful/total*100:.1f}%)")
            print(f"Failed: {failed} ({failed/total*100:.1f}%)")
            print(f"Detailed results saved to: {results_path}")
            print(f"Summary report saved to: {summary_path}")
            
        except Exception as e:
            logging.error(f"Error saving results: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Beatport selectors")
    parser.add_argument("--downloads", action="store_true", help="Test on downloads page (requires login)")
    args = parser.parse_args()
    
    tester = SelectorTester(test_downloads_page=args.downloads)
    tester.run_tests()
