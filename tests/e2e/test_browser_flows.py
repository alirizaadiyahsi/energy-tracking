"""
Browser-based End-to-End Tests for Energy Tracking System
Requires: pip install selenium pytest-asyncio
"""
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Optional
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import configparser


class BrowserE2ETest:
    """Browser-based E2E tests using Selenium"""
    
    def __init__(self, base_url: str = "http://localhost:3000", headless: bool = True):
        self.base_url = base_url.rstrip("/")
        self.headless = headless
        self.driver = None
        self.wait = None
        
        # Load configuration
        config_file = Path(__file__).parent / "config.ini"
        self.config = configparser.ConfigParser()
        if config_file.exists():
            self.config.read(config_file)
        
        # Test data
        self.test_user = {
            "email": self._get_config("test_data", "test_user_email", "browser_test@example.com"),
            "password": self._get_config("test_data", "test_user_password", "BrowserTest123!"),
            "first_name": self._get_config("test_data", "test_user_first_name", "Browser"),
            "last_name": self._get_config("test_data", "test_user_last_name", "TestUser")
        }
        
        self.results = []
    
    def _get_config(self, section: str, key: str, default: str = "") -> str:
        """Get configuration value with default"""
        if self.config.has_section(section) and self.config.has_option(section, key):
            return self.config.get(section, key)
        return default
    
    def setup_driver(self):
        """Setup Chrome WebDriver with options"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Additional Chrome options for stability
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Set implicit wait and explicit wait
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 20)
    
    def teardown_driver(self):
        """Clean up WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def take_screenshot(self, name: str):
        """Take screenshot for debugging"""
        if self.driver:
            screenshot_dir = Path(__file__).parent / "screenshots"
            screenshot_dir.mkdir(exist_ok=True)
            
            timestamp = int(time.time())
            filename = f"{name}_{timestamp}.png"
            filepath = screenshot_dir / filename
            
            self.driver.save_screenshot(str(filepath))
            print(f"Screenshot saved: {filepath}")
    
    def print_colored(self, message: str, color_code: str = "0") -> None:
        """Print colored message"""
        print(f"\033[{color_code}m{message}\033[0m")
    
    async def test_complete_user_journey(self) -> bool:
        """Test complete user journey from registration to analytics"""
        try:
            self.setup_driver()
            
            # Test sequence
            tests = [
                ("test_homepage_load", "Homepage Load"),
                ("test_user_registration", "User Registration"),
                ("test_user_login", "User Login"),
                ("test_dashboard_access", "Dashboard Access"),
                ("test_device_creation", "Device Creation"),
                ("test_device_management", "Device Management"),
                ("test_analytics_view", "Analytics View"),
                ("test_settings_page", "Settings Page"),
                ("test_user_logout", "User Logout"),
            ]
            
            for test_method, test_name in tests:
                self.print_colored(f"Running: {test_name}", "94")
                
                try:
                    method = getattr(self, test_method)
                    result = await method()
                    
                    if result:
                        self.print_colored(f"✅ {test_name} - PASSED", "92")
                        self.results.append((test_name, True, None))
                    else:
                        self.print_colored(f"❌ {test_name} - FAILED", "91")
                        self.results.append((test_name, False, "Test returned False"))
                        self.take_screenshot(f"failed_{test_method}")
                        
                except Exception as e:
                    self.print_colored(f"❌ {test_name} - ERROR: {str(e)}", "91")
                    self.results.append((test_name, False, str(e)))
                    self.take_screenshot(f"error_{test_method}")
                
                # Small delay between tests
                await asyncio.sleep(1)
            
            return all(result[1] for result in self.results)
            
        finally:
            self.teardown_driver()
    
    async def test_homepage_load(self) -> bool:
        """Test homepage loading"""
        try:
            self.driver.get(self.base_url)
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Check if it's the energy tracking app
            title = self.driver.title
            if "energy" not in title.lower() and "tracking" not in title.lower():
                # Look for specific elements that indicate this is our app
                try:
                    self.wait.until(
                        EC.any_of(
                            EC.presence_of_element_located((By.TEXT, "Energy Tracking")),
                            EC.presence_of_element_located((By.CLASS_NAME, "login")),
                            EC.presence_of_element_located((By.ID, "app"))
                        )
                    )
                except TimeoutException:
                    print(f"Page title: {title}")
                    print(f"Page URL: {self.driver.current_url}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"Homepage load error: {e}")
            return False
    
    async def test_user_registration(self) -> bool:
        """Test user registration flow"""
        try:
            # Navigate to registration page
            try:
                # Look for registration link/button
                register_link = self.wait.until(
                    EC.element_to_be_clickable((
                        By.XPATH, 
                        "//a[contains(text(), 'Register') or contains(text(), 'Sign Up')] | //button[contains(text(), 'Register') or contains(text(), 'Sign Up')]"
                    ))
                )
                register_link.click()
            except TimeoutException:
                # Try direct navigation
                self.driver.get(f"{self.base_url}/register")
            
            # Fill registration form
            email_field = self.wait.until(EC.presence_of_element_located((
                By.XPATH, "//input[@type='email' or @name='email' or @id='email']"
            )))
            email_field.clear()
            email_field.send_keys(self.test_user["email"])
            
            password_field = self.driver.find_element(By.XPATH, 
                "//input[@type='password' and (@name='password' or @id='password')]")
            password_field.clear()
            password_field.send_keys(self.test_user["password"])
            
            # Try to find first name field
            try:
                first_name_field = self.driver.find_element(By.XPATH,
                    "//input[@name='firstName' or @name='first_name' or @id='firstName' or @id='first_name']")
                first_name_field.clear()
                first_name_field.send_keys(self.test_user["first_name"])
            except NoSuchElementException:
                pass  # Field might not exist
            
            # Try to find last name field
            try:
                last_name_field = self.driver.find_element(By.XPATH,
                    "//input[@name='lastName' or @name='last_name' or @id='lastName' or @id='last_name']")
                last_name_field.clear()
                last_name_field.send_keys(self.test_user["last_name"])
            except NoSuchElementException:
                pass  # Field might not exist
            
            # Submit form
            submit_button = self.driver.find_element(By.XPATH,
                "//button[@type='submit'] | //input[@type='submit'] | //button[contains(text(), 'Register') or contains(text(), 'Sign Up')]")
            submit_button.click()
            
            # Wait for success or error message
            try:
                # Look for success indicators
                self.wait.until(
                    EC.any_of(
                        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'success') or contains(text(), 'Success')]")),
                        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'registered') or contains(text(), 'Registered')]")),
                        EC.url_contains("login"),
                        EC.url_contains("dashboard")
                    )
                )
                return True
            except TimeoutException:
                # Check for "user already exists" message
                try:
                    error_msg = self.driver.find_element(By.XPATH, 
                        "//*[contains(text(), 'already exists') or contains(text(), 'already registered')]")
                    print("User already exists - continuing")
                    return True
                except NoSuchElementException:
                    return False
            
        except Exception as e:
            print(f"Registration error: {e}")
            return False
    
    async def test_user_login(self) -> bool:
        """Test user login flow"""
        try:
            # Navigate to login page
            self.driver.get(f"{self.base_url}/login")
            
            # Fill login form
            email_field = self.wait.until(EC.presence_of_element_located((
                By.XPATH, "//input[@type='email' or @name='email' or @name='username' or @id='email' or @id='username']"
            )))
            email_field.clear()
            email_field.send_keys(self.test_user["email"])
            
            password_field = self.driver.find_element(By.XPATH,
                "//input[@type='password']")
            password_field.clear()
            password_field.send_keys(self.test_user["password"])
            
            # Submit form
            submit_button = self.driver.find_element(By.XPATH,
                "//button[@type='submit'] | //input[@type='submit'] | //button[contains(text(), 'Login') or contains(text(), 'Sign In')]")
            submit_button.click()
            
            # Wait for redirect to dashboard or success
            self.wait.until(
                EC.any_of(
                    EC.url_contains("dashboard"),
                    EC.url_contains("home"),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Dashboard') or contains(text(), 'Welcome')]"))
                )
            )
            
            return True
            
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    async def test_dashboard_access(self) -> bool:
        """Test dashboard access and basic functionality"""
        try:
            # Ensure we're on dashboard
            if "dashboard" not in self.driver.current_url.lower():
                self.driver.get(f"{self.base_url}/dashboard")
            
            # Wait for dashboard content
            self.wait.until(
                EC.any_of(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Dashboard')]")),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Energy')]")),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Devices')]")),
                )
            )
            
            # Check for typical dashboard elements
            dashboard_elements = [
                "//div[contains(@class, 'dashboard') or contains(@class, 'card') or contains(@class, 'widget')]",
                "//*[contains(text(), 'Total Energy') or contains(text(), 'Energy Consumption')]",
                "//*[contains(text(), 'Devices') or contains(text(), 'Device')]"
            ]
            
            found_elements = 0
            for selector in dashboard_elements:
                try:
                    self.driver.find_element(By.XPATH, selector)
                    found_elements += 1
                except NoSuchElementException:
                    pass
            
            return found_elements > 0
            
        except Exception as e:
            print(f"Dashboard access error: {e}")
            return False
    
    async def test_device_creation(self) -> bool:
        """Test device creation flow"""
        try:
            # Navigate to devices page
            try:
                devices_link = self.driver.find_element(By.XPATH,
                    "//a[contains(text(), 'Devices')] | //button[contains(text(), 'Devices')]")
                devices_link.click()
            except NoSuchElementException:
                self.driver.get(f"{self.base_url}/devices")
            
            # Look for "Add Device" or similar button
            add_button = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//button[contains(text(), 'Add') or contains(text(), 'Create') or contains(text(), 'New')]"
            )))
            add_button.click()
            
            # Fill device form
            name_field = self.wait.until(EC.presence_of_element_located((
                By.XPATH, "//input[@name='name' or @id='name' or @placeholder*='name']"
            )))
            name_field.clear()
            name_field.send_keys("Browser Test Device")
            
            # Try to fill other fields if they exist
            try:
                type_field = self.driver.find_element(By.XPATH,
                    "//select[@name='type'] | //input[@name='type']")
                if type_field.tag_name == "select":
                    from selenium.webdriver.support.ui import Select
                    select = Select(type_field)
                    select.select_by_visible_text("Smart Meter")
                else:
                    type_field.clear()
                    type_field.send_keys("smart_meter")
            except NoSuchElementException:
                pass
            
            try:
                location_field = self.driver.find_element(By.XPATH,
                    "//input[@name='location' or @id='location']")
                location_field.clear()
                location_field.send_keys("Test Location")
            except NoSuchElementException:
                pass
            
            # Submit form
            submit_button = self.driver.find_element(By.XPATH,
                "//button[@type='submit'] | //button[contains(text(), 'Save') or contains(text(), 'Create')]")
            submit_button.click()
            
            # Wait for success
            self.wait.until(
                EC.any_of(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'success') or contains(text(), 'created')]")),
                    EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Browser Test Device')]"))
                )
            )
            
            return True
            
        except Exception as e:
            print(f"Device creation error: {e}")
            return False
    
    async def test_device_management(self) -> bool:
        """Test device listing and management"""
        try:
            # Should be on devices page from previous test
            if "devices" not in self.driver.current_url.lower():
                self.driver.get(f"{self.base_url}/devices")
            
            # Wait for devices list
            self.wait.until(
                EC.presence_of_element_located((By.XPATH, 
                    "//div[contains(@class, 'device')] | //tr[contains(@class, 'device')] | //li[contains(@class, 'device')]"
                ))
            )
            
            # Look for our test device
            test_device = self.driver.find_element(By.XPATH,
                "//*[contains(text(), 'Browser Test Device')]")
            
            # Try to click on device for details
            test_device.click()
            
            # Wait for device details
            self.wait.until(
                EC.any_of(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Device Details')]")),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Browser Test Device')]"))
                )
            )
            
            return True
            
        except Exception as e:
            print(f"Device management error: {e}")
            return False
    
    async def test_analytics_view(self) -> bool:
        """Test analytics page access"""
        try:
            # Navigate to analytics
            try:
                analytics_link = self.driver.find_element(By.XPATH,
                    "//a[contains(text(), 'Analytics')] | //button[contains(text(), 'Analytics')]")
                analytics_link.click()
            except NoSuchElementException:
                self.driver.get(f"{self.base_url}/analytics")
            
            # Wait for analytics content
            self.wait.until(
                EC.any_of(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Analytics')]")),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Chart') or contains(text(), 'Graph')]")),
                    EC.presence_of_element_located((By.XPATH, "//canvas | //*[contains(@class, 'chart')]"))
                )
            )
            
            return True
            
        except Exception as e:
            print(f"Analytics view error: {e}")
            return False
    
    async def test_settings_page(self) -> bool:
        """Test settings page access"""
        try:
            # Navigate to settings
            try:
                settings_link = self.driver.find_element(By.XPATH,
                    "//a[contains(text(), 'Settings')] | //button[contains(text(), 'Settings')]")
                settings_link.click()
            except NoSuchElementException:
                self.driver.get(f"{self.base_url}/settings")
            
            # Wait for settings content
            self.wait.until(
                EC.any_of(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Settings')]")),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Profile')]")),
                    EC.presence_of_element_located((By.XPATH, "//input[@type='email'] | //input[@type='text']"))
                )
            )
            
            return True
            
        except Exception as e:
            print(f"Settings page error: {e}")
            return False
    
    async def test_user_logout(self) -> bool:
        """Test user logout flow"""
        try:
            # Look for logout button/link
            logout_element = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//a[contains(text(), 'Logout') or contains(text(), 'Sign Out')] | //button[contains(text(), 'Logout') or contains(text(), 'Sign Out')]"
            )))
            logout_element.click()
            
            # Wait for redirect to login page
            self.wait.until(
                EC.any_of(
                    EC.url_contains("login"),
                    EC.presence_of_element_located((By.XPATH, "//input[@type='password']"))
                )
            )
            
            return True
            
        except Exception as e:
            print(f"Logout error: {e}")
            return False


async def main():
    """Main entry point for browser E2E tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Browser-based E2E Tests")
    parser.add_argument("--url", default="http://localhost:3000", help="Frontend URL")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    tester = BrowserE2ETest(args.url, args.headless)
    
    try:
        success = await tester.test_complete_user_journey()
        
        # Print summary
        tester.print_colored("\n" + "="*60, "95")
        tester.print_colored("BROWSER E2E TEST SUMMARY", "95")
        tester.print_colored("="*60, "95")
        
        passed = sum(1 for _, result, _ in tester.results if result)
        total = len(tester.results)
        
        tester.print_colored(f"Tests Passed: {passed}/{total}", "92" if passed == total else "91")
        
        for test_name, result, error in tester.results:
            status = "✅ PASSED" if result else "❌ FAILED"
            color = "92" if result else "91"
            tester.print_colored(f"  {test_name}: {status}", color)
            if error and args.verbose:
                tester.print_colored(f"    Error: {error}", "91")
        
        return success
        
    except Exception as e:
        tester.print_colored(f"❌ Browser E2E tests failed: {e}", "91")
        return False


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
