"""
SelectorsManager module for resilient element selection in Beatport scraping.
Handles dynamic selector management, fallback mechanisms, and adaptive learning.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Union, Optional
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException

class SelectorsManager:
    """
    Manages dynamic selectors for Beatport web scraping with resilient element selection.
    Features:
    1. Dynamic selector management for various elements
    2. Fallback mechanisms when primary selectors fail
    3. Adaptive learning from successful selections
    4. Support for both large and small layouts
    5. Detailed logging for debugging
    """
    
    def __init__(self, selectors_file: str = "selectors.json"):
        self.selectors_file = selectors_file
        self.selectors = self.load_selectors()
        self.selector_stats = {}  # Track success/failure of selectors
        
    def load_selectors(self) -> Dict[str, List[str]]:
        """Load selectors from JSON file with fallback to defaults."""
        try:
            with open(self.selectors_file, 'r') as f:
                selectors = json.load(f)
            logging.info("Loaded selectors from selectors.json")
            return selectors
        except Exception as e:
            logging.error(f"Error loading selectors: {e}")
            return {}
            
    def save_selectors(self) -> None:
        """Save current selectors to JSON file."""
        try:
            with open(self.selectors_file, 'w') as f:
                json.dump(self.selectors, f, indent=2)
            logging.info("Saved updated selectors to selectors.json")
        except Exception as e:
            logging.error(f"Error saving selectors: {e}")
            
    def find_element_with_learning(
        self,
        driver: Union[WebDriver, WebElement],
        selector_type: str,
        wait: Optional[WebDriverWait] = None,
        multiple: bool = True,
        context_element: Optional[WebElement] = None
    ) -> Union[List[WebElement], WebElement, None]:
        """
        Find elements using dynamic selector management with learning capabilities.
        
        Args:
            driver: WebDriver or WebElement to search within
            selector_type: Type of element to find (e.g., 'track_containers')
            wait: Optional WebDriverWait for explicit waits
            multiple: Whether to return multiple elements
            context_element: Optional parent element to search within
        
        Returns:
            Found WebElement(s) or None if not found
        """
        if selector_type not in self.selectors:
            logging.error(f"No selectors defined for type: {selector_type}")
            return None
            
        # Initialize stats for this selector type if needed
        if selector_type not in self.selector_stats:
            self.selector_stats[selector_type] = {
                selector: {"hits": 0, "misses": 0}
                for selector in self.selectors[selector_type]
            }
            
        search_element = context_element if context_element else driver
        
        for selector in self.selectors[selector_type]:
            try:
                if wait:
                    elements = wait.until(
                        lambda d: search_element.find_elements(By.CSS_SELECTOR, selector)
                    )
                else:
                    elements = search_element.find_elements(By.CSS_SELECTOR, selector)
                    
                if elements:
                    # Update stats for successful selector
                    self.selector_stats[selector_type][selector]["hits"] += 1
                    
                    if not multiple:
                        return elements[0]
                    return elements
                    
                self.selector_stats[selector_type][selector]["misses"] += 1
                
            except (NoSuchElementException, TimeoutException) as e:
                self.selector_stats[selector_type][selector]["misses"] += 1
                continue
                
        return None
        
    def add_successful_selector(self, selector_type: str, selector: str) -> None:
        """Add a new successful selector to the repertoire."""
        if selector_type not in self.selectors:
            self.selectors[selector_type] = []
            
        if selector not in self.selectors[selector_type]:
            self.selectors[selector_type].insert(0, selector)  # Add to start of list
            self.save_selectors()
            
    def get_selector_stats(self) -> Dict:
        """Get statistics about selector usage and success rates."""
        return self.selector_stats
