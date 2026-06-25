from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import glob
import sys
import random

# ==================== Configuration ====================
download_dir = os.path.join(os.getcwd(), "v2ray_downloads")
os.makedirs(download_dir, exist_ok=True)

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

# Anti-detection arguments
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

# Additional evasion
options.add_argument("--disable-infobars")
options.add_argument("--disable-extensions")
options.add_argument("--profile-directory=Default")
options.add_argument("--disable-plugins-discovery")
options.add_argument("--incognito")

prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True,
    "credentials_enable_service": False,
    "profile.password_manager_enabled": False,
    "profile.default_content_setting_values.notifications": 2
}
options.add_experimental_option("prefs", prefs)

print("🚀 Launching ChromeDriver...")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Execute CDP commands to hide automation
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        window.chrome = {runtime: {}};
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
            Promise.resolve({state: Notification.permission}) :
            originalQuery(parameters)
        );
    """
})

driver.set_page_load_timeout(120)
wait = WebDriverWait(driver, 30)

def human_like_delay(min_sec=1, max_sec=3):
    """Add random delay to simulate human behavior"""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)

def wait_for_cloudflare_to_pass(driver, wait, timeout=180):
    """Wait for Cloudflare challenge to complete"""
    print("🔍 Checking for Cloudflare challenge...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        title = driver.title.lower()
        current_url = driver.current_url.lower()
        
        # Check if we're past Cloudflare
        if "just a moment" not in title and "cloudflare" not in title:
            print(f"✅ Cloudflare challenge passed! Title: {driver.title}")
            return True
        
        # Check if we're redirected
        if "openproxylist.com" in current_url and "just a moment" not in title:
            print(f"✅ Cloudflare passed (URL check)! URL: {current_url}")
            return True
        
        elapsed = int(time.time() - start_time)
        if elapsed % 10 == 0:
            print(f"⏳ Waiting for Cloudflare... ({elapsed}s elapsed)")
        
        time.sleep(2)
    
    print(f"⚠️ Cloudflare timeout after {timeout}s")
    print(f"Final title: {driver.title}")
    print(f"Final URL: {driver.current_url}")
    return False

def get_page_content_alternative():
    """Alternative method to get configs if UI fails"""
    print("🔍 Trying alternative methods to extract configs...")
    
    # Try to get raw text from page
    try:
        page_text = driver.find_element(By.TAG_NAME, "body").text
        print(f"Page text length: {len(page_text)}")
        
        # Look for config patterns
        config_patterns = [
            'vmess://', 'vless://', 'trojan://', 
            'ss://', 'ssr://', 'socks://'
        ]
        
        configs = []
        for line in page_text.split('\n'):
            for pattern in config_patterns:
                if pattern in line.lower():
                    configs.append(line.strip())
                    break
        
        if configs:
            print(f"✅ Found {len(configs)} configs in page text!")
            return configs
    except Exception as e:
        print(f"❌ Error extracting page text: {e}")
    
    return []

try:
    print("⏳ Opening website...")
    driver.get("https://openproxylist.com/v2ray/")
    
    # Wait for Cloudflare to pass
    if not wait_for_cloudflare_to_pass(driver, wait, timeout=120):
        print("❌ Cloudflare challenge not passed, trying alternative approach...")
        
        # Save screenshot for debugging
        driver.save_screenshot("cloudflare_blocked.png")
        
        # Try refreshing
        print("🔄 Refreshing page...")
        driver.refresh()
        time.sleep(30)
        
        if not wait_for_cloudflare_to_pass(driver, wait, timeout=60):
            print("❌ Still blocked by Cloudflare")
            
            # Try alternative method anyway
            configs = get_page_content_alternative()
            if configs:
                merged_file = os.path.join(os.getcwd(), "ALL_V2RAY_CONFIGS.txt")
                with open(merged_file, "w", encoding="utf-8") as f:
                    f.write('\n'.join(configs))
                print(f"✅ Saved {len(configs)} configs from alternative method")
                sys.exit(0)
            else:
                sys.exit(1)
    
    # If we get here, Cloudflare is passed
    print("✅ Page loaded successfully!")
    human_like_delay(5, 10)
    
    page = 1
    max_pages = 50
    
    while page <= max_pages:
        print(f"\n{'='*50}")
        print(f"📄 Processing page {page}")
        print(f"{'='*50}")
        
        human_like_delay(3, 7)
        
        # Try clicking Select All with multiple methods
        select_clicked = False
        for attempt in range(3):
            try:
                # Try finding by different selectors
                selectors = [
                    (By.ID, "select-all"),
                    (By.XPATH, "//button[contains(text(), 'Select All')]"),
                    (By.XPATH, "//*[contains(text(), 'Select All')]"),
                    (By.CSS_SELECTOR, "[id*='select']"),
                ]
                
                for by, selector in selectors:
                    try:
                        elements = driver.find_elements(by, selector)
                        for elem in elements:
                            if elem.is_displayed():
                                driver.execute_script("arguments[0].click();", elem)
                                select_clicked = True
                                print("✅ Select All clicked!")
                                break
                        if select_clicked:
                            break
                    except:
                        continue
                
                if select_clicked:
                    break
                    
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)[:100]}")
                human_like_delay(2, 5)
        
        if not select_clicked:
            print("⚠️ Could not click Select All, trying direct extraction...")
            configs = get_page_content_alternative()
            if configs:
                # Save these configs
                temp_file = os.path.join(download_dir, f"page_{page}.txt")
                with open(temp_file, "w", encoding="utf-8") as f:
                    f.write('\n'.join(configs))
                print(f"✅ Extracted {len(configs)} configs from page source")
        
        human_like_delay(3, 6)
        
        # Try clicking Bulk Download
        download_clicked = False
        for attempt in range(3):
            try:
                download_selectors = [
                    (By.ID, "bulk-download"),
                    (By.XPATH, "//button[contains(text(), 'Bulk Download')]"),
                    (By.XPATH, "//*[contains(text(), 'Download')]"),
                    (By.CSS_SELECTOR, "[id*='download']"),
                ]
                
                for by, selector in download_selectors:
                    try:
                        elements = driver.find_elements(by, selector)
                        for elem in elements:
                            if elem.is_displayed():
                                driver.execute_script("arguments[0].click();", elem)
                                download_clicked = True
                                print("✅ Bulk Download clicked!")
                                break
                        if download_clicked:
                            break
                    except:
                        continue
                
                if download_clicked:
                    break
                    
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)[:100]}")
                human_like_delay(2, 5)
        
        print("⏳ Waiting for download...")
        time.sleep(20)
        
        # Try to find Next button
        next_clicked = False
        next_selectors = [
            "//a[contains(text(), 'Next')]",
            "//button[contains(text(), 'Next')]",
            "//span[contains(text(), 'Next')]",
            "//li[contains(@class, 'next')]//a",
            "//a[contains(@class, 'next')]",
            "//*[contains(@class, 'pagination')]//li[last()]/a",
            "//*[@aria-label='Next']",
        ]
        
        for selector in next_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    if elem.is_displayed():
                        class_attr = elem.get_attribute("class") or ""
                        if "disabled" not in class_attr:
                            driver.execute_script("arguments[0].click();", elem)
                            next_clicked = True
                            print(f"➡️ Next page clicked!")
                            break
                if next_clicked:
                    break
            except:
                continue
        
        if next_clicked:
            page += 1
            human_like_delay(5, 10)
        else:
            print("🛑 No more pages")
            break

    # ==================== Merge Files ====================
    print("\n🔍 Merging downloaded files...")
    time.sleep(5)
    
    txt_files = sorted(glob.glob(os.path.join(download_dir, "*.txt")))
    print(f"📁 Found {len(txt_files)} files")
    
    if txt_files:
        merged_file = os.path.join(os.getcwd(), "ALL_V2RAY_CONFIGS.txt")
        all_configs = []
        
        for file in txt_files:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    lines = content.split('\n')
                    all_configs.extend(lines)
        
        # Remove duplicates
        all_configs = list(dict.fromkeys(all_configs))
        
        with open(merged_file, "w", encoding="utf-8") as f:
            f.write('\n'.join(all_configs))
        
        print(f"✅ Saved {len(all_configs)} unique configs!")
        print(f"📁 Output: {merged_file}")
        print(f"📏 Size: {os.path.getsize(merged_file)} bytes")
        
        if len(all_configs) > 0:
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        # Try alternative: extract directly
        print("⚠️ No files downloaded, trying alternative extraction...")
        configs = get_page_content_alternative()
        
        if configs:
            merged_file = os.path.join(os.getcwd(), "ALL_V2RAY_CONFIGS.txt")
            with open(merged_file, "w", encoding="utf-8") as f:
                f.write('\n'.join(configs))
            print(f"✅ Extracted {len(configs)} configs directly!")
            sys.exit(0)
        else:
            print("❌ No configs found")
            sys.exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

finally:
    driver.quit()
    print("👋 Done")
