from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import glob
import sys
import requests

# ==================== Configuration ====================
download_dir = os.path.join(os.getcwd(), "v2ray_downloads")
os.makedirs(download_dir, exist_ok=True)

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

# Download preferences
prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True,
    "download.extensions_to_open": "",
    "plugins.always_open_pdf_externally": True
}
options.add_experimental_option("prefs", prefs)

print("🚀 Launching ChromeDriver...")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    """
})

# Enable downloads in headless mode
driver.execute_cdp_cmd("Page.setDownloadBehavior", {
    "behavior": "allow",
    "downloadPath": download_dir
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

def get_cookies_dict(driver):
    """Get cookies as dictionary for requests"""
    cookies = {}
    for cookie in driver.get_cookies():
        cookies[cookie['name']] = cookie['value']
    return cookies

def download_configs_page(driver, page_num):
    """Click select all and bulk download, then capture the downloaded file"""
    try:
        # Click Select All
        select_all = wait.until(EC.element_to_be_clickable((By.ID, "select-all")))
        driver.execute_script("arguments[0].click();", select_all)
        print("   ✅ Select All clicked")
        time.sleep(3)
        
        # Click Bulk Download
        bulk_download = wait.until(EC.element_to_be_clickable((By.ID, "bulk-download")))
        driver.execute_script("arguments[0].click();", bulk_download)
        print("   ✅ Bulk Download clicked")
        
        # Wait for download
        print("   ⏳ Waiting for download...")
        time.sleep(15)
        
        # Check for new files
        txt_files = sorted(glob.glob(os.path.join(download_dir, "*.txt")))
        if txt_files:
            print(f"   ✅ Downloaded: {os.path.basename(txt_files[-1])}")
            return True
        else:
            print("   ⚠️ No file downloaded")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:100]}")
        return False

def download_via_api(driver, page_num):
    """Alternative: Try to download using the website's API"""
    try:
        cookies = get_cookies_dict(driver)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        
        # Get CSRF token if exists
        page_source = driver.page_source
        csrf_match = None
        csrf_patterns = [
            r'csrf_token["\']?\s*[:=]\s*["\']([^"\']+)',
            r'name=["\']csrf_token["\']\s+value=["\']([^"\']+)',
        ]
        
        for pattern in csrf_patterns:
            match = __import__('re').search(pattern, page_source)
            if match:
                csrf_match = match.group(1)
                break
        
        # Try different download URLs
        download_urls = [
            f"https://openproxylist.com/v2ray/download?page={page_num}",
            f"https://openproxylist.com/v2ray/export?page={page_num}",
            f"https://openproxylist.com/v2ray/bulk-download?page={page_num}",
        ]
        
        for url in download_urls:
            try:
                data = {}
                if csrf_match:
                    data['csrf_token'] = csrf_match
                
                response = requests.get(url, headers=headers, cookies=cookies, data=data, timeout=30)
                
                if response.status_code == 200 and len(response.text) > 100:
                    filename = os.path.join(download_dir, f"configs_page_{page_num}.txt")
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(response.text)
                    print(f"   ✅ Downloaded via API: {filename}")
                    return True
            except:
                continue
        
        return False
    except Exception as e:
        print(f"   ❌ API download failed: {e}")
        return False

try:
    print("⏳ Opening website...")
    driver.get("https://openproxylist.com/v2ray/")
    
    if not wait_for_page_load(driver, timeout=120):
        print("❌ Page failed to load")
        sys.exit(1)
    
    print("⏳ Waiting for dynamic content...")
    time.sleep(15)
    
    page = 1
    total_downloaded = 0
    
    while page <= 50:
        print(f"\n{'='*50}")
        print(f"📄 Processing page {page}")
        print(f"{'='*50}")
        
        # Method 1: Try normal download
        success = download_configs_page(driver, page)
        
        # Method 2: If normal download failed, try API
        if not success:
            print("   🔄 Trying API download...")
            success = download_via_api(driver, page)
        
        if success:
            total_downloaded += 1
        
        # Find Next button
        next_found = False
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
                            next_found = True
                            print(f"➡️ Moving to page {page + 1}")
                            time.sleep(10)
                            break
                if next_found:
                    break
            except:
                continue
        
        if next_found:
            page += 1
        else:
            print("🛑 No more pages")
            break

    # Merge files
    print(f"\n{'='*50}")
    print("🔍 Merging downloaded files...")
    time.sleep(5)
    
    txt_files = sorted(glob.glob(os.path.join(download_dir, "*.txt")))
    print(f"📁 Found {len(txt_files)} files")
    
    if txt_files:
        merged_file = os.path.join(os.getcwd(), "ALL_V2RAY_CONFIGS.txt")
        with open(merged_file, "w", encoding="utf-8") as outfile:
            for i, file in enumerate(txt_files):
                with open(file, "r", encoding="utf-8") as infile:
                    content = infile.read().strip()
                    if content:
                        outfile.write(content)
                        if i < len(txt_files) - 1:
                            outfile.write("\n")
                print(f"   ✅ {os.path.basename(file)} merged")
        
        print(f"\n✅ Success!")
        print(f"📁 Output: {merged_file}")
        print(f"📏 Size: {os.path.getsize(merged_file)} bytes")
        sys.exit(0)
    else:
        print("❌ No files downloaded")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

finally:
    driver.quit()
    print("👋 Done")
