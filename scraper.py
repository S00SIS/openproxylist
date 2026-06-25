from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import sys
import re

# ==================== Configuration ====================
options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

print("🚀 Launching ChromeDriver...")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Hide automation
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        window.chrome = {runtime: {}};
    """
})

driver.set_page_load_timeout(120)
wait = WebDriverWait(driver, 30)

def wait_for_page_load(driver, timeout=120):
    """Wait for page to load and pass Cloudflare"""
    print("⏳ Waiting for page to load...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        title = driver.title.lower()
        if "just a moment" not in title and "cloudflare" not in title and title != "":
            print(f"✅ Page loaded! Title: {driver.title}")
            return True
        
        elapsed = int(time.time() - start_time)
        if elapsed % 15 == 0:
            print(f"   Still waiting... ({elapsed}s)")
        
        time.sleep(2)
    
    return False

def extract_configs_from_page(driver):
    """Extract proxy configs directly from the page DOM"""
    configs = set()
    
    # Config patterns
    patterns = [
        r'(vmess|vless|trojan|ss|ssr|socks|http|https)://[^\s<>"\'{}|\\^`\[\]]+',
        r'(vmess|vless|trojan|ss|ssr|socks)://[a-zA-Z0-9+/=@:%._~#\[\]!$&\'()*+,;=-]+',
    ]
    
    try:
        # Method 1: Get all text from the page
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        for pattern in patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    # regex returns tuple when groups are used
                    full_match = ''
                    for part in match:
                        full_match += part
                    if len(full_match) > 20:
                        configs.add(full_match)
                elif len(match) > 20:
                    configs.add(match)
        
        # Method 2: Look for code/pre blocks
        code_elements = driver.find_elements(By.TAG_NAME, "code")
        code_elements.extend(driver.find_elements(By.TAG_NAME, "pre"))
        code_elements.extend(driver.find_elements(By.TAG_NAME, "textarea"))
        
        for elem in code_elements:
            try:
                text = elem.text or elem.get_attribute("value") or ""
                for pattern in patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            full_match = ''.join(match)
                            if len(full_match) > 20:
                                configs.add(full_match)
                        elif len(match) > 20:
                            configs.add(match)
            except:
                pass
        
        # Method 3: Get all input values
        inputs = driver.find_elements(By.TAG_NAME, "input")
        for inp in inputs:
            try:
                value = inp.get_attribute("value") or ""
                for pattern in patterns:
                    matches = re.findall(pattern, value, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            full_match = ''.join(match)
                            if len(full_match) > 20:
                                configs.add(full_match)
                        elif len(match) > 20:
                            configs.add(match)
            except:
                pass
        
        # Method 4: Check all links
        links = driver.find_elements(By.TAG_NAME, "a")
        for link in links:
            try:
                href = link.get_attribute("href") or ""
                for pattern in patterns:
                    matches = re.findall(pattern, href, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            full_match = ''.join(match)
                            if len(full_match) > 20:
                                configs.add(full_match)
                        elif len(match) > 20:
                            configs.add(match)
            except:
                pass
                
    except Exception as e:
        print(f"❌ Error extracting configs: {e}")
    
    return list(configs)

def extract_from_tables(driver):
    """Extract configs from table rows"""
    configs = set()
    patterns = [
        r'(vmess|vless|trojan|ss|ssr|socks|http|https)://[^\s<>"\'{}|\\^`\[\]]+',
    ]
    
    try:
        # Find all table rows
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr, .table tbody tr, tr.config-row, .config-item")
        
        for row in rows:
            try:
                row_text = row.text
                for pattern in patterns:
                    matches = re.findall(pattern, row_text, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            full_match = ''.join(match)
                            if len(full_match) > 20:
                                configs.add(full_match)
                        elif len(match) > 20:
                            configs.add(match)
            except:
                pass
    except Exception as e:
        print(f"❌ Error extracting from tables: {e}")
    
    return list(configs)

def click_and_extract(driver, wait):
    """Try clicking elements and extracting configs"""
    all_configs = set()
    
    # Extract without clicking first
    print("📊 Extracting configs from current page...")
    configs = extract_configs_from_page(driver)
    table_configs = extract_from_tables(driver)
    all_configs.update(configs)
    all_configs.update(table_configs)
    print(f"   Found {len(all_configs)} configs from current page")
    
    # Try clicking Select All if exists
    try:
        select_btns = driver.find_elements(By.XPATH, 
            "//*[contains(text(), 'Select All') or contains(text(), 'select all') or @id='select-all']")
        for btn in select_btns:
            try:
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(2)
                break
            except:
                pass
    except:
        pass
    
    # Extract again after clicking
    time.sleep(3)
    configs = extract_configs_from_page(driver)
    table_configs = extract_from_tables(driver)
    all_configs.update(configs)
    all_configs.update(table_configs)
    
    return list(all_configs)

try:
    print("⏳ Opening website...")
    driver.get("https://openproxylist.com/v2ray/")
    
    if not wait_for_page_load(driver, timeout=120):
        print("❌ Page failed to load")
        driver.save_screenshot("error_screenshot.png")
        sys.exit(1)
    
    # Wait extra for dynamic content
    print("⏳ Waiting for dynamic content...")
    time.sleep(15)
    
    all_configs = set()
    page = 1
    max_pages = 20
    
    while page <= max_pages:
        print(f"\n{'='*50}")
        print(f"📄 Processing page {page}")
        print(f"{'='*50}")
        
        # Extract configs from current page
        page_configs = click_and_extract(driver, wait)
        print(f"✅ Extracted {len(page_configs)} configs from page {page}")
        all_configs.update(page_configs)
        
        # Try to find and click Next button
        next_found = False
        next_selectors = [
            "//a[contains(text(), 'Next')]",
            "//button[contains(text(), 'Next')]",
            "//span[contains(text(), 'Next')]",
            "//li[contains(@class, 'next')]//a",
            "//a[contains(@class, 'next')]",
            "//*[contains(@class, 'pagination')]//li[last()]/a",
            "//*[@aria-label='Next']",
            "//a[contains(@href, 'page') and contains(text(), '▶')]",
            "//a[contains(@href, 'page') and contains(text(), '›')]",
        ]
        
        for selector in next_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    if elem.is_displayed():
                        class_attr = elem.get_attribute("class") or ""
                        parent_class = ""
                        try:
                            parent = elem.find_element(By.XPATH, "..")
                            parent_class = parent.get_attribute("class") or ""
                        except:
                            pass
                        
                        if "disabled" not in class_attr and "disabled" not in parent_class:
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                            time.sleep(2)
                            driver.execute_script("arguments[0].click();", elem)
                            next_found = True
                            print(f"➡️ Moving to page {page + 1}")
                            break
                if next_found:
                    break
            except:
                continue
        
        if next_found:
            page += 1
            time.sleep(10)  # Wait for new page to load
        else:
            print("🛑 No more pages found")
            break

    # ==================== Save Results ====================
    print(f"\n{'='*50}")
    print(f"📊 Total unique configs found: {len(all_configs)}")
    
    if all_configs:
        merged_file = os.path.join(os.getcwd(), "ALL_V2RAY_CONFIGS.txt")
        with open(merged_file, "w", encoding="utf-8") as f:
            f.write('\n'.join(sorted(all_configs)))
        
        print(f"✅ Saved to: {merged_file}")
        print(f"📏 File size: {os.path.getsize(merged_file)} bytes")
        
        # Print first few configs as sample
        sample = list(all_configs)[:3]
        print("\n📋 Sample configs:")
        for s in sample:
            print(f"   {s[:100]}...")
        
        sys.exit(0)
    else:
        print("❌ No configs found!")
        print("\nPage source sample:")
        print(driver.page_source[:1000])
        sys.exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

finally:
    driver.quit()
    print("👋 Done")
