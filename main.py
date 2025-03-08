import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import time
import os
import queue
import threading
import json
from datetime import datetime
import traceback  # Added for detailed error tracking
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from pathlib import Path  # For more robust path handling
import json  # For handling selectors.json file
import re

class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record))

class SelectorsManager:
    """Manages selectors with learning capabilities to adapt to website changes"""
    
    def __init__(self):
        self.selectors = self.load_selectors()
        self.selector_stats = {"hits": {}, "misses": {}}
        self.save_path = "selectors.json"
        
    def load_selectors(self):
        """Load selectors from JSON file with fallback defaults"""
        try:
            if os.path.exists('selectors.json'):
                with open('selectors.json', 'r') as f:
                    logging.info("Loaded selectors from selectors.json")
                    return json.load(f)
            else:
                logging.warning("selectors.json not found, using default selectors")
                # Basic default selectors if file doesn't exist
                return {
                    "track_containers": [
                        "[data-testid='library-tracks-table-row']", 
                        "[data-testid='tracks-list-item']"
                    ],
                    "track_name": [
                        "[data-testid='track-title']",
                        ".Tables-shared-style__ReleaseName-sc-792178d5-4",
                        ".TracksList-style__TrackName-sc-921ce1b-0"
                    ],
                    "artist_name": [
                        "[data-testid='artist-name']",
                        "a[href*='/artist/']"
                    ],
                    "download_button": [
                        "svg[data-testid='icon-re-download']",
                        "svg path[stroke='#39C0DE']"
                    ],
                    "pagination": [
                        "[data-testid='pagination-container']"
                    ],
                    "next_button": [
                        "a[data-testid='pagination-next']",
                        "a:has(span:contains('Next'))"
                    ],
                    "popup_download_button": [
                        "//button[contains(text(), 'Download') or .//span[contains(text(), 'Download')]]"
                    ]
                }
        except Exception as e:
            logging.error(f"Error loading selectors: {e}")
            return {}
    
    def update_selector_stats(self, selector_type, selector, success):
        """Track which selectors work and which don't"""
        if success:
            if selector_type not in self.selector_stats["hits"]:
                self.selector_stats["hits"][selector_type] = {}
            if selector not in self.selector_stats["hits"][selector_type]:
                self.selector_stats["hits"][selector_type][selector] = 0
            self.selector_stats["hits"][selector_type][selector] += 1
        else:
            if selector_type not in self.selector_stats["misses"]:
                self.selector_stats["misses"][selector_type] = {}
            if selector not in self.selector_stats["misses"][selector_type]:
                self.selector_stats["misses"][selector_type][selector] = 0
            self.selector_stats["misses"][selector_type][selector] += 1
    
    def find_element_with_learning(self, driver, selector_type, context_element=None, multiple=True, wait=None):
        """Find element(s) with automatic selector learning"""
        if selector_type not in self.selectors:
            logging.warning(f"No selectors defined for {selector_type}")
            return [] if multiple else None
        
        # Try selectors in order (with the most successful ones first)
        successful_selector = None
        elements = []
        
        for selector in self.selectors[selector_type]:
            try:
                # Try CSS selector first
                try:
                    if context_element:
                        if multiple:
                            found_elements = context_element.find_elements(By.CSS_SELECTOR, selector)
                        else:
                            found_element = context_element.find_element(By.CSS_SELECTOR, selector)
                            found_elements = [found_element] if found_element else []
                    elif wait:
                        if multiple:
                            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                            found_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        else:
                            found_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                            found_elements = [found_element] if found_element else []
                    else:
                        if multiple:
                            found_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        else:
                            found_element = driver.find_element(By.CSS_SELECTOR, selector)
                            found_elements = [found_element] if found_element else []
                except Exception:
                    # If CSS selector fails, try XPath
                    try:
                        if context_element:
                            if multiple:
                                found_elements = context_element.find_elements(By.XPATH, selector)
                            else:
                                found_element = context_element.find_element(By.XPATH, selector)
                                found_elements = [found_element] if found_element else []
                        elif wait:
                            if multiple:
                                wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                                found_elements = driver.find_elements(By.XPATH, selector)
                            else:
                                found_element = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                                found_elements = [found_element] if found_element else []
                        else:
                            if multiple:
                                found_elements = driver.find_elements(By.XPATH, selector)
                            else:
                                found_element = driver.find_element(By.XPATH, selector)
                                found_elements = [found_element] if found_element else []
                    except Exception:
                        found_elements = []
                
                # Only count visible elements
                visible_elements = [e for e in found_elements if e.is_displayed()]
                
                if visible_elements:
                    successful_selector = selector
                    elements = visible_elements
                    self.update_selector_stats(selector_type, selector, True)
                    
                    # If we found elements, rearrange the selectors to put this one first
                    if successful_selector != self.selectors[selector_type][0]:
                        self.selectors[selector_type].remove(successful_selector)
                        self.selectors[selector_type].insert(0, successful_selector)
                        self.save_selectors()  # Save updated selectors
                    
                    break
                else:
                    self.update_selector_stats(selector_type, selector, False)
            except Exception as e:
                self.update_selector_stats(selector_type, selector, False)
                logging.debug(f"Selector failed: {selector} - {str(e)}")
        
        if not elements:
            logging.debug(f"No elements found for selector type: {selector_type}")
            
        return elements if multiple else (elements[0] if elements else None)
                
    def save_selectors(self):
        """Save updated selectors to JSON file"""
        try:
            # Only save if we've made changes
            with open(self.save_path, 'w') as f:
                json.dump(self.selectors, f, indent=2)
            logging.debug("Saved updated selectors")
        except Exception as e:
            logging.error(f"Error saving selectors: {e}")
    
    def add_selector(self, selector_type, new_selector):
        """Add a new selector that was found to work"""
        if selector_type not in self.selectors:
            self.selectors[selector_type] = []
        
        if new_selector not in self.selectors[selector_type]:
            self.selectors[selector_type].insert(0, new_selector)
            self.save_selectors()
            logging.info(f"Added new working selector for {selector_type}: {new_selector}")
    
    def verify_selectors_health(self, driver, wait):
        """Test if critical selectors still work and log warnings for broken ones"""
        try:
            logging.info("Running selector health check...")
            working_selectors = {}
            broken_selectors = {}
            
            # Test track container selectors
            for selector_type in ["track_containers", "track_name", "artist_name", "download_button"]:
                elements = self.find_element_with_learning(driver, selector_type, wait=wait)
                if elements:
                    working_selectors[selector_type] = True
                else:
                    broken_selectors[selector_type] = True
            
            # Log results
            if broken_selectors:
                logging.warning("Some selectors appear to be broken and need updating:")
                for key in broken_selectors:
                    logging.warning(f"- {key}: No working selectors found")
            else:
                logging.info("All selectors appear to be healthy")
                
            return len(broken_selectors) == 0
        except Exception as e:
            logging.error(f"Error during selector health check: {e}")
            return False

class BeatportUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Beatport Track Finder")
        self.window.geometry("800x600")
        
        # Create main frames
        self.input_frame = ttk.Frame(self.window)
        self.input_frame.pack(padx=10, pady=5, fill=tk.X)
        
        self.log_frame = ttk.Frame(self.window)
        self.log_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        # Input fields
        self.create_input_fields()
        
        # Log display
        self.create_log_display()
        
        # Continue button (initially hidden)
        self.continue_button = ttk.Button(self.window, text="Continue After Login", 
                                        command=self.continue_after_login)
        self.continue_button.pack(pady=5)
        self.continue_button.pack_forget()
        
        # Save Report Button (initially hidden)
        self.save_report_button = ttk.Button(self.window, text="Save Failed Downloads Report", 
                                           command=self.save_failed_downloads_report)
        self.save_report_button.pack(pady=5)
        self.save_report_button.pack_forget()
        
        # Queue for log messages
        self.log_queue = queue.Queue()
        self.setup_logging()
        
        # Start queue checking
        self.check_queue()
        
        self.finder = None
        self.processing_thread = None
        
        # Load saved preferences
        self.load_preferences()

    def create_input_fields(self):
        # Left column
        left_frame = ttk.Frame(self.input_frame)
        left_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(left_frame, text="Start Page:").pack(pady=2)
        self.start_page = ttk.Entry(left_frame, width=10)
        self.start_page.pack(pady=2)
        self.start_page.insert(0, "1")
        
        ttk.Label(left_frame, text="End Page:").pack(pady=2)
        self.end_page = ttk.Entry(left_frame, width=10)
        self.end_page.pack(pady=2)
        
        # Middle column
        middle_frame = ttk.Frame(self.input_frame)
        middle_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(middle_frame, text="Check downloads page after? (y/n):").pack(pady=2)
        self.check_downloads = ttk.Entry(middle_frame, width=10)
        self.check_downloads.pack(pady=2)
        self.check_downloads.insert(0, "y")
        
        # Right column
        right_frame = ttk.Frame(self.input_frame)
        right_frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Label(right_frame, text="Download Location:").pack(pady=2)
        location_frame = ttk.Frame(right_frame)
        location_frame.pack(fill=tk.X, pady=2)
        
        self.download_location = ttk.Entry(location_frame)
        self.download_location.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(location_frame, text="Browse", 
                   command=self.browse_download_location).pack(side=tk.RIGHT, padx=5)
        
        # Multiple Downloads checkbox
        self.multiple_downloads = tk.BooleanVar(value=True)
        ttk.Checkbutton(right_frame, text="Enable Multiple Simultaneous Downloads", 
                       variable=self.multiple_downloads).pack(pady=5)
        
        # Process Downloads Page Only checkbox
        self.downloads_page_only = tk.BooleanVar(value=False)
        ttk.Checkbutton(right_frame, text="Process Downloads Page Only (Skip Library Pages)", 
                       variable=self.downloads_page_only).pack(pady=5)
        
        # Start Button
        ttk.Button(right_frame, text="Start Processing", 
                  command=self.start_processing).pack(pady=5)

    def create_log_display(self):
        self.log_display = scrolledtext.ScrolledText(self.log_frame, height=20)
        self.log_display.pack(fill=tk.BOTH, expand=True)

    def setup_logging(self):
        queue_handler = QueueHandler(self.log_queue)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        queue_handler.setFormatter(formatter)
        
        logger = logging.getLogger()
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)

    def check_queue(self):
        while True:
            try:
                record = self.log_queue.get_nowait()
                self.log_display.insert(tk.END, record + '\n')
                self.log_display.see(tk.END)
                self.window.update_idletasks()
            except queue.Empty:
                break
        self.window.after(100, self.check_queue)

    def load_preferences(self):
        try:
            if os.path.exists('preferences.json'):
                with open('preferences.json', 'r') as f:
                    prefs = json.load(f)
                    if 'download_location' in prefs:
                        self.download_location.delete(0, tk.END)
                        self.download_location.insert(0, prefs['download_location'])
        except Exception as e:
            logging.error(f"Error loading preferences: {e}")

    def save_preferences(self):
        try:
            prefs = {
                'download_location': self.download_location.get()
            }
            with open('preferences.json', 'w') as f:
                json.dump(prefs, f)
        except Exception as e:
            logging.error(f"Error saving preferences: {e}")

    def browse_download_location(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_location.delete(0, tk.END)
            self.download_location.insert(0, folder)
            self.save_preferences()

    def save_failed_downloads_report(self):
        if not self.finder or not self.finder.failed_downloads:
            messagebox.showinfo("Info", "No failed downloads to report.")
            return

        try:
            filename = f"failed_downloads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = os.path.join(self.download_location.get(), filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("Failed Downloads Report\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Total Failed Downloads: {len(self.finder.failed_downloads)}\n\n")
                
                for track in self.finder.failed_downloads:
                    f.write(f"Track: {track['name']}\n")
                    f.write(f"Artist: {track['artist']}\n")
                    f.write(f"Reason: {track['reason']}\n")
                    f.write(f"Page: {track['page']}\n")
                    f.write("-" * 50 + "\n")

            logging.info(f"Failed downloads report saved to: {filepath}")
            messagebox.showinfo("Success", f"Report saved to:\n{filepath}")
        except Exception as e:
            logging.error(f"Error saving failed downloads report: {e}")
            messagebox.showerror("Error", "Failed to save the report. Check logs for details.")

    def validate_inputs(self):
        try:
            # If "Process Downloads Page Only" is checked, we don't need to validate start and end pages
            if self.downloads_page_only.get():
                check_downloads = self.check_downloads.get().lower()
                download_location = self.download_location.get()
                
                if check_downloads not in ['y', 'n']:
                    messagebox.showerror("Error", "Please enter 'y' or 'n' for downloads check")
                    return False

                if not download_location:
                    messagebox.showerror("Error", "Please select a download location")
                    return False

                if not os.path.exists(download_location):
                    messagebox.showerror("Error", "The specified download location does not exist")
                    return False
                
                return True
            else:
                # Normal validation when processing library pages
                start = int(self.start_page.get())
                end = int(self.end_page.get())
                check_downloads = self.check_downloads.get().lower()
                download_location = self.download_location.get()

                if start < 1 or end < start:
                    messagebox.showerror("Error", "Invalid page numbers")
                    return False

                if check_downloads not in ['y', 'n']:
                    messagebox.showerror("Error", "Please enter 'y' or 'n' for downloads check")
                    return False

                if not download_location:
                    messagebox.showerror("Error", "Please select a download location")
                    return False

                if not os.path.exists(download_location):
                    messagebox.showerror("Error", "The specified download location does not exist")
                    return False

                return True

        except ValueError:
            # If "Process Downloads Page Only" is checked, we don't need to validate start and end pages
            if self.downloads_page_only.get():
                # Re-run validation without checking start/end pages
                return self.validate_inputs()
            else:
                messagebox.showerror("Error", "Please enter valid numbers for start and end pages")
                return False

    def start_processing(self):
        if not self.validate_inputs():
            return
            
        self.disable_inputs()
        self.processing_thread = threading.Thread(target=self.process_in_thread)
        self.processing_thread.start()

    def process_in_thread(self):
        try:
            # If downloads_page_only is checked, we don't need start_page and end_page
            if self.downloads_page_only.get():
                self.finder = BeatportTrackFinder(
                    1,  # Default value for start_page
                    1,  # Default value for end_page
                    self.check_downloads.get().lower() == 'y',
                    self.download_location.get(),
                    self.multiple_downloads.get(),
                    self.downloads_page_only.get()
                )
            else:
                self.finder = BeatportTrackFinder(
                    int(self.start_page.get()),
                    int(self.end_page.get()),
                    self.check_downloads.get().lower() == 'y',
                    self.download_location.get(),
                    self.multiple_downloads.get(),
                    self.downloads_page_only.get()
                )
            
            self.window.after(0, self.show_continue_button)
            self.finder.initialize_browser()
            
        except Exception as e:
            logging.error(f"Error during processing: {e}")
            self.window.after(0, self.enable_inputs)

    def show_continue_button(self):
        self.continue_button.pack(pady=5)
        logging.info("Please log in and click 'Continue After Login' when ready...")

    def continue_after_login(self):
        self.continue_button.pack_forget()
        threading.Thread(target=self.continue_processing).start()

    def continue_processing(self):
        try:
            self.finder.click_next_and_process()
        except Exception as e:
            logging.error(f"Error during processing: {e}")
        finally:
            self.window.after(0, self.enable_inputs)

    def disable_inputs(self):
        for widget in [self.start_page, self.end_page, self.check_downloads, 
                      self.download_location]:
            widget.configure(state='disabled')

    def enable_inputs(self):
        for widget in [self.start_page, self.end_page, self.check_downloads, 
                      self.download_location]:
            widget.configure(state='normal')
        if self.finder and self.finder.failed_downloads:
            self.save_report_button.pack(pady=5)

class BeatportTrackFinder:
    def __init__(self, start_page, end_page, check_downloads, download_location, multiple_downloads, downloads_page_only=False):
        self.start_page = start_page
        self.end_page = end_page
        self.check_downloads = check_downloads
        self.download_location = download_location
        self.multiple_downloads = multiple_downloads
        self.downloads_page_only = downloads_page_only
        self.successful_downloads = 0
        self.failed_downloads = []
        self.current_page = 1
        self.driver = None
        self.wait = None
        
        # Initialize selector manager for resilient element selection
        self.selector_manager = SelectorsManager()
        
    def initialize_browser(self):
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-notifications")
        
        prefs = {
            "profile.default_content_setting_values.automatic_downloads": 1,
            "download.default_directory": self.download_location,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "download.default_directory": os.path.abspath(self.download_location),
            "download.prompt_for_download": False,
            "profile.default_content_settings.popups": 0,
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.automatic_downloads": 1,
            "profile.content_settings.pattern_pairs.*.multiple-automatic-downloads": 1
        }
        
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-notifications")
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), 
                                     options=chrome_options)
        
        params = {'behavior': 'allow', 'downloadPath': self.download_location}
        self.driver.execute_cdp_cmd('Page.setDownloadBehavior', params)
        
        self.wait = WebDriverWait(self.driver, 20)
        
        # Open directly to downloads page if downloads_page_only is enabled
        if self.downloads_page_only:
            logging.info("Opening directly to downloads page (Downloads Page Only mode)")
            self.driver.get("https://www.beatport.com/library/downloads?page=1&per_page=100")
        else:
            self.driver.get("https://www.beatport.com/library?name=")

    def navigate_to_my_library(self):
        try:
            # Navigate to login page first
            self.driver.get("https://www.beatport.com/account/login")
            logging.info("Navigated to login page")
            
            # Wait for user to manually log in
            logging.info("Please log in manually. The script will continue after login...")
            
            # Wait until the URL changes to something other than the login page
            try:
                WebDriverWait(self.driver, 120).until(
                    lambda driver: "account/login" not in driver.current_url
                )
                logging.info("Login detected, continuing...")
            except TimeoutException:
                logging.warning("Login timeout. Please log in faster next time.")
                return False
            
            # Navigate to correct library page
            if self.downloads_page_only:
                self.driver.get("https://www.beatport.com/library/downloads")
                logging.info("Navigated to Downloads page")
            else:
                self.driver.get("https://www.beatport.com/library")
                logging.info("Navigated to Library page")
            
            # Allow time for the page to load
            time.sleep(3)
            return True
        except Exception as e:
            logging.error(f"Error navigating to library: {e}")
            return False

    def handle_download_popup(self):
        """Handle any download popups that appear after clicking download"""
        try:
            # Wait a moment for any popup to appear
            time.sleep(1)
            
            # Use selector manager to find the "Download" button in popups
            popup_buttons = self.selector_manager.find_element_with_learning(
                self.driver, 
                'popup_download_button', 
                wait=self.wait, 
                multiple=True
            )
            
            if popup_buttons:
                # Click the first matching button
                download_button = popup_buttons[0]
                self.driver.execute_script("arguments[0].click();", download_button)
                logging.info("Clicked download button in popup")
                return True
                
            # Fallback: Look for buttons with specific text content
            try:
                # Look for buttons that contain "Download" text
                popup_buttons = self.driver.find_elements(
                    By.XPATH, 
                    "//button[contains(text(), 'Download') or .//span[contains(text(), 'Download')]]"
                )
                
                if popup_buttons:
                    # Click the first matching button
                    download_button = popup_buttons[0]
                    self.driver.execute_script("arguments[0].click();", download_button)
                    
                    # If this worked, add to selector manager
                    self.selector_manager.add_selector(
                        'popup_download_button', 
                        "//button[contains(text(), 'Download') or .//span[contains(text(), 'Download')]]"
                    )
                    
                    logging.info("Clicked text-based download button in popup")
                    return True
            except Exception as e:
                logging.debug(f"Text-based popup button detection failed: {e}")
                
            # Fallback: Try to find modal containing download options
            try:
                # Look for modal dialogs
                modals = self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    "[role='dialog'], .modal, .dialog, .popup"
                )
                
                for modal in modals:
                    # Try to find download buttons within the modal
                    buttons = modal.find_elements(By.TAG_NAME, "button")
                    for btn in buttons:
                        btn_text = btn.text.lower()
                        if "download" in btn_text and not "don't" in btn_text and not "cancel" in btn_text:
                            self.driver.execute_script("arguments[0].click();", btn)
                            
                            # If this worked, add to selector manager
                            self.selector_manager.add_selector(
                                'popup_download_button', 
                                f".{' '.join(btn.get_attribute('class').split())}"
                            )
                            
                            logging.info("Clicked download button in modal")
                            return True
            except Exception as e:
                logging.debug(f"Modal dialog detection failed: {e}")
                
            # If no popup detected, that's okay - some tracks don't have popups
            return False
                
        except Exception as e:
            logging.error(f"Error handling download popup: {e}")
            return False

    def find_track_containers(self):
        """Find track containers based on the current page layout with adaptive selector learning"""
        try:
            # Wait for track containers to be present using our selector manager
            track_containers = self.selector_manager.find_element_with_learning(
                self.driver, 
                'track_containers', 
                wait=self.wait
            )
            
            if track_containers:
                # Determine layout type based on attributes of the found elements
                sample = track_containers[0]
                if 'library-tracks-table-row' in sample.get_attribute('data-testid') or 'table' in sample.get_attribute('class').lower():
                    layout_type = 'large'
                else:
                    layout_type = 'small'
                    
                logging.info(f"Found {len(track_containers)} track containers using {layout_type} screen layout")
                return track_containers, layout_type
            
            logging.warning("No track containers found with any selector")
            return [], None
            
        except Exception as e:
            logging.error(f"Error finding track containers: {e}")
            traceback.print_exc()  # More detailed error tracking
            return [], None

    def download_tracks_from_page(self):
        try:
            # Wait for track containers to be present
            self.wait.until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, 
                    "[data-testid='library-tracks-table-row'], [data-testid='tracks-list-item']"
                ))
            )
            
            track_containers, layout_type = self.find_track_containers()
            
            if not track_containers:
                logging.error("No track containers found on the page")
                return False
                
            logging.info(f"Found {len(track_containers)} tracks to download (layout: {layout_type})")

            for index, track in enumerate(track_containers, 1):
                try:
                    # Use different approaches based on layout type
                    if layout_type == "small":
                        success = self.download_track_small_layout(track, index)
                    else:
                        success = self.download_track_large_layout(track, index)
                        
                    if success:
                        continue
                    # Method 1: Try the exact XPath for download button (specific to the downloads page)
                    try:
                        # Use the exact XPath provided
                        download_buttons = track.find_elements(
                            By.XPATH, 
                            ".//button[./svg[contains(@viewBox, '0 0 16 16') and .//path[contains(@stroke, '#39C0DE')]]]"
                        )
                        
                        if download_buttons:
                            download_button = download_buttons[0]
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", download_button)
                            time.sleep(0.5)
                            self.driver.execute_script("arguments[0].click();", download_button)
                            
                            self.handle_download_popup()
                            
                            track_name = self.extract_track_name(track, layout_type)
                            logging.info(f"Started download for: {track_name} (using XPath method)")
                            self.successful_downloads += 1
                            time.sleep(1)
                            continue
                    except Exception as e:
                        logging.debug(f"Method 1 failed: {e}")
                    
                    # Method 2: Look for button with blue SVG path
                    try:
                        # Try to find button with stroke="#39C0DE" in the path
                        download_buttons = track.find_elements(
                            By.XPATH, 
                            ".//button[.//path[@stroke='#39C0DE']]"
                        )
                        
                        if download_buttons:
                            download_button = download_buttons[0]
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", download_button)
                            time.sleep(0.5)
                            self.driver.execute_script("arguments[0].click();", download_button)
                            
                            self.handle_download_popup()
                            
                            track_name = self.extract_track_name(track, layout_type)
                            logging.info(f"Started download for: {track_name} (using blue path method)")
                            self.successful_downloads += 1
                            time.sleep(1)
                            continue
                    except Exception as e:
                        logging.debug(f"Method 2 failed: {e}")
                        
                    # Method 3: Try to find the re-download icon button
                    try:
                        redownload_buttons = track.find_elements(
                            By.XPATH,
                            ".//button[.//svg[@data-testid='icon-re-download']]"
                        )
                        
                        if redownload_buttons:
                            download_button = redownload_buttons[0]
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", download_button)
                            time.sleep(0.5)
                            self.driver.execute_script("arguments[0].click();", download_button)
                            
                            self.handle_download_popup()
                            
                            track_name = self.extract_track_name(track, layout_type)
                            logging.info(f"Started download for: {track_name} (using re-download method)")
                            self.successful_downloads += 1
                            time.sleep(1)
                            continue
                    except Exception as e:
                        logging.debug(f"Method 3 failed: {e}")
                    
                    # Method 4: Try to find any button in the download-actions div
                    try:
                        action_buttons = track.find_elements(
                            By.XPATH,
                            ".//div[contains(@class, 'download-actions')]/button"
                        )
                        
                        if action_buttons:
                            download_button = action_buttons[0]
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", download_button)
                            time.sleep(0.5)
                            self.driver.execute_script("arguments[0].click();", download_button)
                            
                            self.handle_download_popup()
                            
                            track_name = self.extract_track_name(track, layout_type)
                            logging.info(f"Started download for: {track_name} (using download-actions method)")
                            self.successful_downloads += 1
                            time.sleep(1)
                            continue
                    except Exception as e:
                        logging.debug(f"Method 4 failed: {e}")
                        
                    # Method 5: Last-ditch effort - try to find any button SVG
                    try:
                        svg_buttons = track.find_elements(By.XPATH, ".//button[.//svg]")
                        
                        for btn in svg_buttons:
                            # Skip if it has a disabled attribute
                            if btn.get_attribute("disabled"):
                                continue
                                
                            btn_html = btn.get_attribute("outerHTML").lower()
                            # Look for clues that this might be a download button
                            if "download" in btn_html or "39c0de" in btn_html or "#39c0de" in btn_html:
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                time.sleep(0.5)
                                self.driver.execute_script("arguments[0].click();", btn)
                                
                                self.handle_download_popup()
                                
                                track_name = self.extract_track_name(track, layout_type)
                                logging.info(f"Started download for: {track_name} (using fallback method)")
                                self.successful_downloads += 1
                                time.sleep(1)
                                break
                    except Exception as e:
                        logging.debug(f"Method 5 failed: {e}")
                    
                    # If we get here, we couldn't find any download button
                    track_name = self.extract_track_name(track, layout_type)
                    logging.warning(f"No download button found for track: {track_name}")
                    self.failed_downloads.append({
                        'name': track_name,
                        'artist': self.extract_artist_name(track, layout_type),
                        'reason': "No download button found",
                        'page': self.current_page
                    })

                except Exception as e:
                    track_name = self.extract_track_name(track, layout_type)
                    artist_name = self.extract_artist_name(track, layout_type)
                    error_msg = str(e)
                    logging.error(f"Failed to download track: {track_name} - {error_msg}")
                    self.failed_downloads.append({
                        'name': track_name,
                        'artist': artist_name,
                        'reason': f"Download failed: {error_msg}",
                        'page': self.current_page
                    })

            return True
        except Exception as e:
            logging.error(f"Error in download_tracks_from_page: {e}")
            return False

    def find_pagination(self):
        try:
            # Try to find pagination wrapper using the updated class
            pagination = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "[class*='Pager-style__Wrapper']")
            ))
            logging.info("Found pagination container")

            # Find total pages
            total_pages = None
            try:
                # Try to find the last page number
                page_items = pagination.find_elements(By.CSS_SELECTOR, "[class*='lithw']")
                for item in page_items:
                    if '...' in item.text:
                        disabled_element = item.find_element(By.CLASS_NAME, "disabled")
                        total_pages = int(disabled_element.text)
                        logging.info(f"Found total pages: {total_pages}")
                        break
            except:
                logging.info("Could not determine total pages")

            # Find next button
            next_button = None
            try:
                next_button = pagination.find_element(
                    By.XPATH, ".//a[.//span[contains(text(), 'Next')]]"
                )
                if next_button:
                    next_url = next_button.get_attribute('href')
                    logging.info(f"Found next page URL: {next_url}")
            except:
                logging.info("No next button found")

            return {
                'total_pages': total_pages,
                'next_button': next_button
            }
        except Exception as e:
            logging.error(f"Error finding pagination: {e}")
            return None

    def process_page(self, page_number):
        try:
            self.current_page = page_number
            
            # Wait for tracks to load
            self.wait.until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, 
                    "[data-testid='library-tracks-table-row'], [data-testid='tracks-list-item']"
                ))
            )
            
            track_containers, layout_type = self.find_track_containers()

            if not track_containers:
                logging.error(f"No tracks found on page {page_number}")
                return False

            logging.info(f"\nProcessing page {page_number}")
            logging.info("="*50)
            logging.info(f"Found {len(track_containers)} tracks")
            logging.info("="*50 + "\n")

            for index, track in enumerate(track_containers, 1):
                try:
                    track_name = self.extract_track_name(track, layout_type)
                    artist_name = self.extract_artist_name(track, layout_type)
                    svg_status = self.extract_svg_status(track, layout_type)

                    logging.info(
                        f"Track {index}/{len(track_containers)}:\n"
                        f"Title: {track_name}\n"
                        f"Artist: {artist_name}\n"
                        f"Status: {svg_status}\n"
                        f"{'-' * 50}"
                    )

                    if svg_status == "Available for Download":
                        try:
                            # Find the re-download icon
                            download_button = None
                            
                            try:
                                download_button = track.find_element(By.CSS_SELECTOR, "svg[data-testid='icon-re-download']")
                            except:
                                # Look for the download button with the blue path
                                download_button = track.find_element(
                                    By.CSS_SELECTOR, 
                                    "svg path[stroke='#39C0DE']"
                                ).find_element(By.XPATH, "./..")
                                
                            if download_button:
                                parent_button = download_button.find_element(By.XPATH, "./..")
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", parent_button)
                                time.sleep(0.5)
                                self.driver.execute_script("arguments[0].click();", parent_button)
                                
                                self.handle_download_popup()
                                
                                self.successful_downloads += 1
                                logging.info(f"[SUCCESS] Added to downloads: {track_name}")
                                time.sleep(0.5)
                                
                        except Exception as e:
                            error_msg = str(e)
                            logging.error(f"[FAILED] Could not add to downloads: {track_name}")
                            logging.error(f"Error: {error_msg}")
                            self.failed_downloads.append({
                                'name': track_name,
                                'artist': artist_name,
                                'reason': f"Download button click failed: {error_msg}",
                                'page': self.current_page
                            })
                    else:
                        self.failed_downloads.append({
                            'name': track_name,
                            'artist': artist_name,
                            'reason': f"Track status: {svg_status}",
                            'page': self.current_page
                        })

                except Exception as e:
                    logging.error(f"Error processing track {index} on page {page_number}: {e}")
                    self.failed_downloads.append({
                        'name': f"Unknown Track {index}",
                        'artist': "Unknown Artist",
                        'reason': f"Processing error: {str(e)}",
                        'page': self.current_page
                    })

            return True
        except Exception as e:
            logging.error(f"Error processing page {page_number}: {e}")
            return False

    def check_downloads_page(self):
        try:
            self.driver.get("https://www.beatport.com/library/downloads?page=1&per_page=100")
            time.sleep(8)  # Increased wait time for page to load (5-10 seconds as recommended)

            # Try processing downloads multiple times to ensure all are caught
            attempts = 0
            max_attempts = 5  # Increased from 3 to 5 attempts
            previous_successful_count = self.successful_downloads  # Initialize to track new downloads
            
            while attempts < max_attempts:
                logging.info(f"Download attempt {attempts + 1}/{max_attempts}")
                result = self.download_tracks_from_page()
                
                if not result:
                    logging.warning("Download attempt failed, retrying after refresh")
                
                time.sleep(5)  # Wait for downloads to start
                logging.info("Refreshing downloads page...")
                self.driver.refresh()  # Reload the page to check for remaining tracks
                time.sleep(8)  # Increased wait after refresh to ensure all tracks are loaded

                # After refreshing, use the same comprehensive download method as initially
                logging.info("Checking for more tracks to download after refresh...")
                
                # Use the same download_tracks_from_page method that's used initially
                result = self.download_tracks_from_page()
                
                if not result:
                    logging.info("No more tracks found to download after refresh")
                    break
                
                # Check if we actually downloaded any tracks in this attempt
                if attempts > 0 and self.successful_downloads == previous_successful_count:
                    logging.info("No new tracks were downloaded in this attempt, stopping")
                    break
                    
                # Store the current successful count to check in the next iteration
                previous_successful_count = self.successful_downloads
                    
                attempts += 1
                
            logging.info("Download page processing complete")

        except Exception as e:
            logging.error(f"Error in check_downloads_page: {e}")
            # Try to capture a screenshot if possible
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = os.path.join(self.download_location, f"error_screenshot_{timestamp}.png")
                self.driver.save_screenshot(screenshot_path)
                logging.info(f"Error screenshot saved to: {screenshot_path}")
            except:
                pass

    def click_next_and_process(self):
        try:
            # If downloads_page_only is enabled, skip library pages processing
            if self.downloads_page_only:
                logging.info("Downloads Page Only mode enabled - skipping library pages processing")
                self.check_downloads_page()
                return
                
            current_page = 1

            # Navigate to the start page
            while current_page < self.start_page:
                logging.info(f"Navigating to page {current_page + 1}")
                
                # More precise next button locator
                next_button = self.wait.until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//a[contains(@class, 'Pager-style__Page') and .//span[text()='Next']]")
                    )
                )
                
                # Ensure we're clicking the button and not something else
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                time.sleep(1)
                
                # Get current URL before clicking
                current_url = self.driver.current_url
                
                # Click with JavaScript to avoid accidental clicks
                self.driver.execute_script("arguments[0].click();", next_button)
                
                # Wait for page to change
                try:
                    WebDriverWait(self.driver, 10).until(
                        lambda driver: driver.current_url != current_url
                    )
                    time.sleep(3)  # Additional wait to ensure page loads
                    current_page += 1
                except:
                    logging.error(f"Failed to navigate to page {current_page + 1}, retrying...")
                    # Try clicking again after a short wait
                    time.sleep(2)
                    self.driver.execute_script("arguments[0].click();", next_button)
                    WebDriverWait(self.driver, 10).until(
                        lambda driver: driver.current_url != current_url
                    )
                    time.sleep(3)
                    current_page += 1

            # Process pages from start_page to end_page
            while current_page <= self.end_page:
                logging.info(f"Processing page {current_page}")
                self.process_page(current_page)

                if current_page == self.end_page:
                    break

                # Navigate to next page
                try:
                    # Try to find the next button using the selector manager
                    next_buttons = self.selector_manager.find_element_with_learning(
                        self.driver, 
                        'next_button', 
                        wait=self.wait, 
                        multiple=True
                    )
                    
                    if not next_buttons:
                        logging.warning("No next button found using selector manager, trying fallback methods")
                        
                        # Fallback method 1: Try to find by text content
                        try:
                            next_button = self.driver.find_element(
                                By.XPATH, 
                                "//a[contains(@class, 'Pager') and .//span[text()='Next']]"
                            )
                            
                            # If found, add to our selector manager for future use
                            self.selector_manager.add_selector(
                                'next_button', 
                                "//a[contains(@class, 'Pager') and .//span[text()='Next']]"
                            )
                            next_buttons = [next_button]
                        except NoSuchElementException:
                            pass
                            
                        # Fallback method 2: Try to find by aria-label
                        if not next_buttons:
                            try:
                                next_button = self.driver.find_element(
                                    By.CSS_SELECTOR, 
                                    "a[aria-label='Next page']"
                                )
                                
                                # If found, add to our selector manager for future use
                                self.selector_manager.add_selector(
                                    'next_button', 
                                    "a[aria-label='Next page']"
                                )
                                next_buttons = [next_button]
                            except NoSuchElementException:
                                pass
                                
                        # Fallback method 3: Try to find by icon
                        if not next_buttons:
                            try:
                                next_button = self.driver.find_element(
                                    By.XPATH, 
                                    "//a[.//svg[contains(@class, 'icon-arrow-right') or contains(@class, 'icon-next')]]"
                                )
                                
                                # If found, add to our selector manager for future use
                                self.selector_manager.add_selector(
                                    'next_button', 
                                    "//a[.//svg[contains(@class, 'icon-arrow-right') or contains(@class, 'icon-next')]]"
                                )
                                next_buttons = [next_button]
                            except NoSuchElementException:
                                pass
            
                    if next_buttons:
                        next_button = next_buttons[0]
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                        time.sleep(0.5)
                        
                        # Check if button is disabled
                        disabled = next_button.get_attribute("disabled") or next_button.get_attribute("aria-disabled") == "true"
                        if disabled:
                            logging.info("Next button is disabled, we're on the last page")
                            return False
                        
                        # Click the next button
                        self.driver.execute_script("arguments[0].click();", next_button)
                        
                        # Wait for page to load after clicking next
                        time.sleep(2)
                        
                        # Check if page URL has changed
                        if "page=" in self.driver.current_url:
                            page_param = re.search(r"page=(\d+)", self.driver.current_url)
                            if page_param:
                                new_page = int(page_param.group(1))
                                if new_page != self.current_page:
                                    self.current_page = new_page
                                    logging.info(f"Successfully navigated to page {self.current_page}")
                                    return True
                        
                        # If no page indicator in URL, assume we moved to the next page
                        self.current_page += 1
                        logging.info(f"Navigated to next page (assumed page {self.current_page})")
                        return True
                        
                    logging.warning("No next button found on page - either we're on the last page or there's a website layout change")
                    return False
                    
                except Exception as e:
                    logging.error(f"Navigation error: {e} - trying again")
                    time.sleep(5)  # Wait longer before retry
                    
                    # Try one more time with a different approach
                    try:
                        # Try to find the next button again
                        next_button = self.driver.find_element(
                            By.XPATH, 
                            "//a[contains(@class, 'Pager-style__Page') and .//span[contains(text(), 'Next')]]"
                        )
                        current_url = self.driver.current_url
                        
                        # Try clicking the parent element instead
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                        time.sleep(2)
                        self.driver.execute_script("arguments[0].click();", next_button)
                        
                        WebDriverWait(self.driver, 15).until(
                            lambda driver: driver.current_url != current_url
                        )
                        time.sleep(3)
                        current_page += 1
                    except Exception as second_error:
                        logging.error(f"Failed to navigate after retry: {second_error}")
                        raise

            # Check downloads page if enabled
            if self.check_downloads and not self.downloads_page_only:
                logging.info("\nChecking downloads page...")
                self.check_downloads_page()

        except Exception as e:
            logging.error(f"Error in click_next_and_process: {e}")
        finally:
            logging.info(f"\nProcessing Summary:")
            logging.info("=" * 50)
            logging.info(f"Total successful downloads added: {self.successful_downloads}")
            logging.info(f"Total failed downloads: {len(self.failed_downloads)}")
            logging.info("=" * 50)

    def download_track_large_layout(self, track, index):
        """Handle download for large screen layout"""
        try:
            # Use selector manager to find download button
            download_buttons = self.selector_manager.find_element_with_learning(
                self.driver, 
                'download_button', 
                context_element=track
            )
            
            if download_buttons:
                download_button = download_buttons[0]
                parent = download_button
                
                # Try to find the parent button if we got the SVG
                try:
                    if download_button.tag_name.lower() in ['svg', 'path']:
                        parent = download_button.find_element(By.XPATH, "./ancestor::button")
                except:
                    # If we can't find a parent button, use the element itself
                    pass
                    
                # Scroll and click
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", parent)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", parent)
                
                self.handle_download_popup()
                
                track_name = self.extract_track_name(track, "large")
                logging.info(f"Started download for: {track_name} (using adaptive selector)")
                self.successful_downloads += 1
                time.sleep(1)
                return True
                
            # If selector manager failed, try visual recognition approaches
            # Look for buttons with blue SVG paths
            try:
                blue_path_buttons = track.find_elements(
                    By.XPATH, 
                    ".//button[.//path[@stroke='#39C0DE' or contains(@stroke, '39C0DE') or @fill='#39C0DE' or contains(@fill, '39C0DE')]]"
                )
                
                if blue_path_buttons:
                    button = blue_path_buttons[0]
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", button)
                    
                    self.handle_download_popup()
                    
                    # If this worked, add it to our selectors
                    self.selector_manager.add_selector(
                        'download_button', 
                        ".//button[.//path[@stroke='#39C0DE' or contains(@stroke, '39C0DE')]]"
                    )
                    
                    track_name = self.extract_track_name(track, "large")
                    logging.info(f"Started download for: {track_name} (using blue path method)")
                    self.successful_downloads += 1
                    time.sleep(1)
                    return True
            except Exception as e:
                logging.debug(f"Blue path button method failed: {e}")
                
            return False
                
        except Exception as e:
            logging.error(f"Error downloading track with large layout: {e}")
            return False

    def download_track_small_layout(self, track, index):
        """Handle download for small screen layout"""
        try:
            # Use selector manager to find download button
            download_buttons = self.selector_manager.find_element_with_learning(
                self.driver, 
                'download_button', 
                context_element=track
            )
            
            if download_buttons:
                download_button = download_buttons[0]
                parent = download_button
                
                # Try to find the parent button if we got the SVG
                try:
                    if download_button.tag_name.lower() in ['svg', 'path']:
                        parent = download_button.find_element(By.XPATH, "./ancestor::button")
                except:
                    # If we can't find a parent button, use the element itself
                    pass
                    
                # Scroll and click
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", parent)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", parent)
                
                self.handle_download_popup()
                
                track_name = self.extract_track_name(track, "small")
                logging.info(f"Started download for: {track_name} (using adaptive selector)")
                self.successful_downloads += 1
                time.sleep(1)
                return True
                
            # If selector manager failed, try finding any button with blue SVG or icons
            try:
                buttons = track.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    btn_html = button.get_attribute("outerHTML").lower()
                    if 'download' in btn_html or '39c0de' in btn_html or 'svg' in btn_html:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                        time.sleep(0.5)
                        self.driver.execute_script("arguments[0].click();", button)
                        
                        self.handle_download_popup()
                        
                        # If this worked, add it to our selectors
                        self.selector_manager.add_selector(
                            'download_button', 
                            "button:contains('download')"
                        )
                        
                        track_name = self.extract_track_name(track, "small")
                        logging.info(f"Started download for: {track_name} (using button scan method)")
                        self.successful_downloads += 1
                        time.sleep(1)
                        return True
            except Exception as e:
                logging.debug(f"Button scan method failed: {e}")
                
            return False
                
        except Exception as e:
            logging.error(f"Error downloading track with small layout: {e}")
            return False
            
    def extract_track_name(self, track, layout_type):
        try:
            # Use selector manager to find track name
            name_element = self.selector_manager.find_element_with_learning(
                self.driver, 
                'track_name', 
                context_element=track, 
                multiple=False
            )
            
            if name_element:
                return name_element.text
                
            # Visual recognition fallback: look for any element that might contain the track name
            title_links = track.find_elements(By.CSS_SELECTOR, "a[title]:not([title=''])") 
            if title_links:
                for link in title_links:
                    if '/track/' in link.get_attribute('href'):
                        return link.get_attribute('title')
                        
            # Structure recognition fallback: try to find h2/h3/h4 elements that might be track names
            for tag in ['h2', 'h3', 'h4', 'strong']:
                elements = track.find_elements(By.TAG_NAME, tag)
                if elements:
                    return elements[0].text
                    
            return "Track name not found"

        except Exception as e:
            logging.error(f"Error extracting track name: {e}")
            return "Track name not found"

    def extract_artist_name(self, track, layout_type):
        try:
            # Use selector manager to find artist name
            artist_elements = self.selector_manager.find_element_with_learning(
                self.driver, 
                'artist_name', 
                context_element=track
            )
            
            if artist_elements:
                artist_names = [elem.text for elem in artist_elements if elem.text.strip()]
                if artist_names:
                    return ", ".join(artist_names)
            
            # Structural fallback: look for artist links by href pattern
            artist_links = track.find_elements(By.CSS_SELECTOR, "a[href*='/artist/']")
            artist_names = [link.text for link in artist_links if link.text.strip()]
            if artist_names:
                return ", ".join(artist_names)
                
            # Visual recognition fallback: any small text next to the track name might be artists
            small_texts = track.find_elements(By.TAG_NAME, "small")
            if small_texts:
                return small_texts[0].text

            return "Artist name not found"

        except Exception as e:
            logging.error(f"Error extracting artist name: {e}")
            return "Artist name not found"

    def extract_svg_status(self, track, layout_type):
        try:
            # Check for re-download icon 
            try:
                re_download_svg = track.find_element(By.CSS_SELECTOR, "svg[data-testid='icon-re-download']")
                return "Available for Download"
            except:
                pass
                
            # Look for download finished icon
            try:
                download_finished_svg = track.find_element(By.CSS_SELECTOR, "svg[data-testid='icon-download-finished']")
                return "Already Downloaded"
            except:
                pass
                
            # Look for blue download button on downloads page
            try:
                download_button = track.find_element(
                    By.XPATH, 
                    ".//button/svg[contains(@viewBox, '0 0 16 16') and contains(@stroke, '#39C0DE')]"
                )
                return "Available for Download"
            except:
                pass
                
            # Additional check for small layout
            if layout_type == "small":
                try:
                    # Look for any button with blue path in small layout
                    blue_paths = track.find_elements(
                        By.XPATH,
                        ".//path[contains(@stroke, '#39') or contains(@fill, '#39')]"
                    )
                    if blue_paths:
                        return "Available for Download"
                except:
                    pass
                
            return "No Download Status Found"
            
        except Exception as e:
            logging.error(f"Error determining download status: {e}")
            return "Error Determining Status"

    def start_download(self):
        try:
            self.initialize_browser()
            self.wait = WebDriverWait(self.driver, 10)
            
            # Navigate to library page with login handling
            if not self.navigate_to_my_library():
                logging.error("Failed to navigate to library page")
                return False
            
            if self.end_page is None:
                self.end_page = self.start_page
                
            current_page = 1
            
            # If we're not starting from page 1, navigate to the start page
            if self.start_page > 1:
                # Construct the URL with the correct page parameter
                if self.downloads_page_only:
                    self.driver.get(f"https://www.beatport.com/library/downloads?page={self.start_page}")
                else:
                    self.driver.get(f"https://www.beatport.com/library?page={self.start_page}")
                current_page = self.start_page
                logging.info(f"Navigated to start page {current_page}")
                self.current_page = current_page
                time.sleep(2)  # Wait for page to load
            
            # Process each page
            while current_page <= self.end_page:
                logging.info(f"Processing page {current_page} of {self.end_page}")
                
                # Download tracks from current page
                self.download_tracks_from_page()
                
                # Stop if we've reached the end page
                if current_page >= self.end_page:
                    logging.info(f"Reached target end page {current_page}")
                    break
                
                # Navigate to next page
                if not self.click_next_and_process():
                    logging.info("No more pages available or navigation failed")
                    break
                    
                current_page = self.current_page  # Update from the class property
            
            # Print summary
            logging.info(f"\nProcessing Summary:")
            logging.info("=" * 50)
            logging.info(f"Total successful downloads added: {self.successful_downloads}")
            logging.info(f"Total failed downloads: {len(self.failed_downloads)}")
            logging.info("=" * 50)
            
            return True
            
        except Exception as e:
            logging.error(f"Error in download process: {e}")
            traceback.print_exc()
            return False
            
        finally:
            if self.driver:
                self.driver.quit()

def main():
    app = BeatportUI()
    app.window.mainloop()

if __name__ == "__main__":
    main()
