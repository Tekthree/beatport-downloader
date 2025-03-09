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
from datetime import datetime

# Import the SelectorsManager from main.py
import sys
sys.path.append(str(Path(__file__).parent))
from main import SelectorsManager

class SelectorTester:
    def __init__(self, test_downloads_page=False):
        self.test_downloads_page = test_downloads_page
        self.driver = None
        self.wait = None
        self.selector_manager = SelectorsManager()
        self.test_results = {
            "large_screen": {},
            "small_screen": {},
            "timestamp": datetime.now().isoformat(),
            "url_tested": None,
            "screen_sizes_tested": {
                "large": {"width": 1920, "height": 1080},
                "small": {"width": 768, "height": 900}
            }
        }
        
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
                
                # After login, check if we're redirected to the library page
                current_url = self.driver.current_url
                logging.info(f"Redirected to: {current_url}")
                
                # Take a screenshot for debugging
                screenshot_path = Path(__file__).parent / "login_redirect.png"
                self.driver.save_screenshot(str(screenshot_path))
                logging.info(f"Saved screenshot to {screenshot_path}")
                
                return True
            except TimeoutException:
                logging.error("Login timeout expired. Test cannot continue without login.")
                return False
                
        except Exception as e:
            logging.error(f"Error during login process: {e}")
            traceback.print_exc()
            return False
            
    def find_downloads_page(self):
        """Try multiple approaches to find and navigate to the downloads page"""
        try:
            logging.info("Attempting to find and navigate to downloads page...")
            
            # Take a screenshot before navigation attempts
            screenshot_path = Path(__file__).parent / "before_downloads_nav.png"
            self.driver.save_screenshot(str(screenshot_path))
            logging.info(f"Saved screenshot to {screenshot_path}")
            
            # Approach 1: Direct URL
            self.driver.get("https://www.beatport.com/library/downloads")
            time.sleep(3)
            if "downloads" in self.driver.current_url:
                logging.info("Successfully navigated to downloads page via direct URL")
                return True
                
            # Approach 2: Look for navigation menu items
            try:
                logging.info("Looking for navigation menu items...")
                # Try to find any menu items or navigation elements
                nav_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    "nav a, .navigation a, .menu a, .sidebar a, header a, a[href*='downloads']")
                
                for element in nav_elements:
                    try:
                        href = element.get_attribute("href") or ""
                        text = element.text.lower()
                        logging.info(f"Found navigation element: {text} (href: {href})")
                        
                        if "download" in href or "download" in text:
                            logging.info(f"Clicking element with text: {text}, href: {href}")
                            # Scroll to element and click
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                            time.sleep(1)
                            element.click()
                            time.sleep(3)
                            
                            if "downloads" in self.driver.current_url:
                                logging.info("Successfully navigated to downloads page via menu")
                                return True
                    except Exception as e:
                        logging.debug(f"Error with navigation element: {e}")
                        continue
            except Exception as e:
                logging.error(f"Error finding navigation elements: {e}")
            
            # Approach 3: Try to find tabs or secondary navigation
            try:
                logging.info("Looking for tab elements...")
                # Navigate to main library page first
                self.driver.get("https://www.beatport.com/library")
                time.sleep(3)
                
                # Look for tab elements or secondary navigation
                tab_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    ".tabs a, .tab a, ul.navigation a, .sub-nav a, .secondary-nav a")
                
                for tab in tab_elements:
                    try:
                        href = tab.get_attribute("href") or ""
                        text = tab.text.lower()
                        logging.info(f"Found tab element: {text} (href: {href})")
                        
                        if "download" in href or "download" in text:
                            logging.info(f"Clicking tab with text: {text}, href: {href}")
                            # Scroll to element and click
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", tab)
                            time.sleep(1)
                            tab.click()
                            time.sleep(3)
                            
                            if "downloads" in self.driver.current_url:
                                logging.info("Successfully navigated to downloads page via tab")
                                return True
                    except Exception as e:
                        logging.debug(f"Error with tab element: {e}")
                        continue
            except Exception as e:
                logging.error(f"Error finding tab elements: {e}")
            
            # If all approaches fail, take a screenshot for debugging
            screenshot_path = Path(__file__).parent / "failed_downloads_nav.png"
            self.driver.save_screenshot(str(screenshot_path))
            logging.info(f"Saved failure screenshot to {screenshot_path}")
            
            logging.warning("All approaches to find downloads page failed")
            return False
            
        except Exception as e:
            logging.error(f"Error finding downloads page: {e}")
            traceback.print_exc()
            return False
            
    def navigate_to_test_page(self):
        """Navigate to the appropriate page for testing selectors"""
        try:
            # Explicitly log the current URL before navigation
            current_url = self.driver.current_url
            logging.info(f"Current URL before navigation: {current_url}")
            
            # Navigate to the appropriate page based on test type
            if self.test_downloads_page:
                if not self.find_downloads_page():
                    logging.error("Failed to navigate to downloads page")
                    return False
            else:
                target_url = "https://www.beatport.com/library"
                self.driver.get(target_url)
                logging.info(f"Attempting to navigate to Library page: {target_url}")
                
            # Wait for page to load properly
            time.sleep(5)  # Increased wait time
            
            # Verify we're on the correct page
            current_url = self.driver.current_url
            logging.info(f"Current URL after navigation: {current_url}")
            
            if self.test_downloads_page and "downloads" not in current_url:
                logging.warning("Failed to navigate to downloads page. Check if you're properly logged in.")
                
                # Try one more time with a different approach
                logging.info("Trying alternative navigation to downloads page...")
                self.driver.get("https://www.beatport.com/library")
                time.sleep(2)
                
                try:
                    # Look for a link to the downloads page
                    downloads_link = self.driver.find_element(By.XPATH, "//a[contains(@href, '/downloads') or contains(text(), 'Downloads')]")
                    logging.info("Found downloads link, clicking it...")
                    downloads_link.click()
                    time.sleep(3)
                    
                    current_url = self.driver.current_url
                    logging.info(f"URL after clicking downloads link: {current_url}")
                    
                    if "downloads" in current_url:
                        logging.info("Successfully navigated to downloads page via link")
                        return True
                except Exception as e:
                    logging.error(f"Failed to find downloads link: {e}")
                
                return False
                
            return True
            
        except Exception as e:
            logging.error(f"Error navigating to test page: {e}")
            traceback.print_exc()
            return False
    
    def set_window_size(self, size_type):
        """Set window size based on type (large or small)"""
        try:
            sizes = self.test_results["screen_sizes_tested"][size_type]
            self.driver.set_window_size(sizes["width"], sizes["height"])
            time.sleep(2)  # Allow time for layout to adjust
            
            # Take screenshot of new window size
            screenshot_path = Path(__file__).parent / f"{size_type}_screen_layout.png"
            self.driver.save_screenshot(str(screenshot_path))
            logging.info(f"Set window size to {size_type} screen ({sizes['width']}x{sizes['height']})")
            logging.info(f"Screenshot saved to: {screenshot_path}")
            
            # Save page source for this layout
            html_path = Path(__file__).parent / f"{size_type}_screen_source.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            logging.info(f"Page source for {size_type} screen saved to: {html_path}")
            
            return True
        except Exception as e:
            logging.error(f"Error setting {size_type} window size: {e}")
            traceback.print_exc()
            return False
            
    def test_selector(self, selector_type, context_element=None, multiple=True, screen_size="large"):
        """Test a specific selector type"""
        try:
            logging.info(f"Testing {selector_type} selector on {screen_size} screen...")
            result = {
                "success": False,
                "selector_used": None,
                "error": None,
                "count": 0,
                "screen_size": screen_size
            }
            
            try:
                elements = self.selector_manager.find_element_with_learning(
                    self.driver if not context_element else context_element,
                    selector_type,
                    wait=self.wait,
                    multiple=multiple
                )
                
                if elements:
                    if not multiple and not isinstance(elements, list):
                        elements = [elements]
                    result["success"] = True
                    result["count"] = len(elements)
                    
                    # Find which selector worked by checking the stats
                    selector_stats = self.selector_manager.selector_stats.get(selector_type, {})
                    for selector, stats in selector_stats.items():
                        if stats['hits'] > 0:
                            result["selector_used"] = selector
                            break
                            
                    logging.info(f"Successfully found {result['count']} element(s) using selector: {result['selector_used']}")
                else:
                    result["error"] = "No elements found"
                    logging.warning(f"No elements found for {selector_type} on {screen_size} screen")
            except Exception as e:
                result["error"] = str(e)
                logging.error(f"Error testing {selector_type} on {screen_size} screen: {e}")
            
            return result
            
        except Exception as e:
            logging.error(f"Error in test_selector for {selector_type} on {screen_size} screen: {e}")
            traceback.print_exc()
            return {"success": False, "error": str(e), "screen_size": screen_size}
    
    def run_tests(self):
        """Run tests for all selectors on both screen sizes"""
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
                
            # Store the URL we're testing on
            self.test_results["url_tested"] = self.driver.current_url
            logging.info(f"Testing on URL: {self.test_results['url_tested']}")
            
            # Test on large screen first
            logging.info("Starting large screen tests...")
            if not self.set_window_size("large"):
                logging.error("Failed to set large screen size")
                return False
                
            self.test_results["large_screen"] = self.run_screen_size_tests("large")
            
            # Test on small screen
            logging.info("Starting small screen tests...")
            if not self.set_window_size("small"):
                logging.error("Failed to set small screen size")
                return False
                
            self.test_results["small_screen"] = self.run_screen_size_tests("small")
            
            # Save final results
            self.save_results()
            
            return True
            
        except Exception as e:
            logging.error(f"Error running tests: {e}")
            traceback.print_exc()
            return False
            
        finally:
            if self.driver:
                self.driver.quit()
                
    def run_screen_size_tests(self, screen_size):
        """Run all selector tests for a specific screen size"""
        results = {}
        
        try:
            # Test track containers selector first
            results["track_containers"] = self.test_selector("track_containers", screen_size=screen_size)
            
            if not results["track_containers"]["success"]:
                logging.warning(f"No track containers found on {screen_size} screen. The page might be empty.")
                # Still test other selectors at page level
                results["track_name"] = self.test_selector("track_name", multiple=False, screen_size=screen_size)
                results["artist_name"] = self.test_selector("artist_name", screen_size=screen_size)
                results["download_button"] = self.test_selector("download_button", screen_size=screen_size)
                # Skip pagination test as there are no tracks
                results["next_button"] = {
                    "success": True,
                    "count": 0,
                    "error": "Pagination not tested - no tracks found",
                    "screen_size": screen_size,
                    "selector_used": None
                }
                return results
            
            # Get number of tracks to determine if pagination should exist
            track_containers = self.selector_manager.find_element_with_learning(
                self.driver, "track_containers", wait=self.wait
            )
            track_count = len(track_containers) if track_containers else 0
            logging.info(f"Found {track_count} tracks on {screen_size} screen")
            
            # Test track-level selectors on first container
            if track_containers and len(track_containers) > 0:
                sample_container = track_containers[0]
                results["track_name"] = self.test_selector(
                    "track_name", context_element=sample_container, multiple=False, screen_size=screen_size
                )
                results["artist_name"] = self.test_selector(
                    "artist_name", context_element=sample_container, screen_size=screen_size
                )
                results["download_button"] = self.test_selector(
                    "download_button", context_element=sample_container, screen_size=screen_size
                )
            
            # Only test pagination if we have enough tracks
            # Beatport typically shows 10-20 tracks per page
            TRACKS_PER_PAGE = 10
            if track_count >= TRACKS_PER_PAGE:
                logging.info(f"Testing pagination with {track_count} tracks")
                results["next_button"] = self.test_selector("next_button", screen_size=screen_size)
            else:
                logging.info(f"Skipping pagination test - only {track_count} tracks found (need {TRACKS_PER_PAGE})")
                results["next_button"] = {
                    "success": True,
                    "count": 0,
                    "error": f"Pagination not tested - only {track_count} tracks found",
                    "screen_size": screen_size,
                    "selector_used": None
                }
            
            return results
            
        except Exception as e:
            logging.error(f"Error running {screen_size} screen tests: {e}")
            traceback.print_exc()
            return results
    
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
                
                for screen_size, results in self.test_results.items():
                    if screen_size in ["large_screen", "small_screen"]:
                        f.write(f"=== {screen_size} Screen Results ===\n\n")
                        for selector_type, result in results.items():
                            if result["success"]:
                                successful += 1
                                status = "✓ SUCCESS"
                            else:
                                failed += 1
                                status = "✗ FAILED"
                                
                            f.write(f"{status} - {selector_type}:\n")
                            f.write(f"  Found: {result['count']} element(s)\n")
                            
                            if result["selector_used"]:
                                f.write(f"  Working selector: {result['selector_used']}\n")
                            
                            if result["error"]:
                                f.write(f"  Error: {result['error']}\n")
                                
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
    # Set up logging to both file and console
    log_file = Path(__file__).parent / "selector_test.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Beatport selectors")
    parser.add_argument('--downloads', action='store_true', help='Test selectors on downloads page')
    args = parser.parse_args()
    
    logging.info("Starting selector tests...")
    logging.info(f"Testing on downloads page: {args.downloads}")
    
    tester = SelectorTester(test_downloads_page=args.downloads)
    success = tester.run_tests()
    
    if success:
        logging.info("Tests completed. Check selector_test_report.json and selector_test_summary.txt for results")
    else:
        logging.error("Tests failed. Check logs for details")
