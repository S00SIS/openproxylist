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
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
options.add_experimental_option("prefs", prefs)

print("🚀 Launching ChromeDriver...")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
driver.set_page_load_timeout(120)  # Increase page load timeout
wait = WebDriverWait(driver, 30)

def wait_for_table_load(driver, wait):
    """Wait for the proxy table to load completely"""
    print("🔍 Waiting for table to load...")
    
    # Different selectors to try
    selectors = [
        "table",
        "#v2ray-table",
        ".table",
        "tbody tr",
        ".config-table"
    ]
    
    table_found = False
    for selector in selectors:
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            print(f"✅ Table found using selector: {selector}")
            table_found = True
            break
        except:
            continue
    
    if not table_found:
        print("⚠️ Could not find table with any selector")
        print(f"Page source snippet: {driver.page_source[:500]}")
    
    return table_found

def click_element_safely(driver, wait, element_id, element_name):
    """Safely click an element with multiple fallback methods"""
    methods = [
        # Method 1: Wait for element to be clickable and click
        lambda: wait.until(EC.element_to_be_clickable((By.ID, element_id))).click(),
        
        # Method 2: Scroll into view and click
        lambda: (
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", 
                                 driver.find_element(By.ID, element_id)),
            time.sleep(2),
            driver.find_element(By.ID, element_id).click()
        ),
        
        # Method 3: JavaScript click
        lambda: driver.execute_script(f"document.getElementById('{element_id}').click();"),
        
        # Method 4: Force click with JavaScript
        lambda: driver.execute_script(f"""
            var element = document.getElementById('{element_id}');
            if(element) {{
                element.style.display = 'block';
                element.style.visibility = 'visible';
                element.disabled = false;
                element.click();
            }}
        """),
    ]
    
    for i, method in enumerate(methods, 1):
        try:
            print(f"   Attempting method {i} for {element_name}...")
            method()
            print(f"   ✅ {element_name} clicked successfully with method {i}")
            return True
        except Exception as e:
            print(f"   ❌ Method {i} failed: {str(e)[:100]}")
            time.sleep(2)
            continue
    
    return False

try:
    print("⏳ Opening website...")
    driver.get("https://openproxylist.com/v2ray/")
    
    # Wait for page to load
    print("⏳ Waiting 60 seconds for initial page load...")
    time.sleep(60)
    
    # Take screenshot for debugging (optional)
    try:
        driver.save_screenshot("page_loaded.png")
        print("📸 Screenshot saved as page_loaded.png")
    except:
        pass
    
    # Print page info
    print(f"📄 Page title: {driver.title}")
    print(f"🔗 Current URL: {driver.current_url}")
    
    # Wait for table
    wait_for_table_load(driver, wait)
    time.sleep(15)
    
    page = 1
    max_pages = 50  # Safety limit
    
    while page <= max_pages:
        print(f"\n{'='*50}")
        print(f"📄 Processing page {page}")
        print(f"{'='*50}")
        
        # Additional wait for dynamic content
        print("⏳ Waiting 20 seconds for dynamic content...")
        time.sleep(20)
        
        # ====== Select All ======
        print("🔍 Looking for Select All button...")
        select_success = click_element_safely(driver, wait, "select-all", "Select All")
        
        if not select_success:
            print("❌ Could not click Select All after all attempts")
            # Try to find what elements exist on the page
            all_elements = driver.find_elements(By.XPATH, "//*[@id]")
            ids = [elem.get_attribute('id') for elem in all_elements if elem.get_attribute('id')]
            print(f"Available IDs on page: {ids[:20]}")
            
            # If no select-all, maybe we're done
            if page == 1:
                print("⚠️ First page failed. Exiting...")
                sys.exit(1)
            break
        
        print("⏳ Waiting 15 seconds after Select All...")
        time.sleep(15)
        
        # ====== Bulk Download ======
        print("🔍 Looking for Bulk Download button...")
        download_success = click_element_safely(driver, wait, "bulk-download", "Bulk Download")
        
        if not download_success:
            print("❌ Could not click Bulk Download after all attempts")
            break
        
        # Wait for download
        print("⏳ Waiting 30 seconds for download to complete...")
        time.sleep(30)
        
        # ====== Check for Next Page ======
        print("🔍 Looking for Next button...")
        next_found = False
        
        next_selectors = [
            "//a[contains(text(), 'Next')]",
            "//button[contains(text(), 'Next')]",
            "//span[contains(text(), 'Next')]",
            "//li[contains(@class, 'next')]//a",
            "//a[contains(@class, 'next')]",
            "//button[contains(@class, 'next')]",
            "//*[contains(@class, 'pagination')]//a[last()]",
            "//*[contains(@class, 'pagination')]//li[last()]/a",
        ]
        
        for selector in next_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        class_attr = element.get_attribute("class") or ""
                        if "disabled" not in class_attr:
                            print(f"   Found Next button with selector: {selector}")
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                            time.sleep(5)
                            element.click()
                            next_found = True
                            break
                if next_found:
                    break
            except:
                continue
        
        if next_found:
            print(f"➡️ Moving to page {page + 1}")
            page += 1
            time.sleep(15)
        else:
            print("🛑 No more pages found")
            break

    print("\n" + "="*50)
    print(f"✅ Finished processing {page} pages")
    print("="*50)

    # ==================== Merge Files ====================
    print("\n🔍 Searching for downloaded files...")
    time.sleep(10)
    
    # List all files in download directory
    all_files = os.listdir(download_dir)
    print(f"📁 All files in download directory: {all_files}")
    
    txt_files = sorted(glob.glob(os.path.join(download_dir, "*.txt")))
    print(f"📁 Number of txt files found: {len(txt_files)}")
    
    if txt_files:
        merged_file = os.path.join(os.getcwd(), "ALL_V2RAY_CONFIGS.txt")
        total_configs = 0
        
        with open(merged_file, "w", encoding="utf-8") as outfile:
            for i, file in enumerate(txt_files):
                with open(file, "r", encoding="utf-8") as infile:
                    content = infile.read().strip()
                    if content:
                        lines = content.split('\n')
                        total_configs += len(lines)
                        outfile.write(content)
                        if i < len(txt_files) - 1:
                            outfile.write("\n")
                print(f"   ✅ {os.path.basename(file)} merged ({os.path.getsize(file)} bytes)")

        print(f"\n{'='*50}")
        print(f"🎉 Success!")
        print(f"📊 Total configs: {total_configs}")
        print(f"📁 Output: {merged_file}")
        print(f"📏 File size: {os.path.getsize(merged_file)} bytes")
        print(f"{'='*50}")
        
        if total_configs == 0:
            print("⚠️ Warning: 0 configs found!")
            sys.exit(1)
    else:
        print("⚠️ No txt files found!")
        print("This might be because:")
        print("1. Site structure changed")
        print("2. Download didn't work in headless mode")
        print("3. Site blocking automated access")
        
        # Try to find any downloaded files
        all_downloads = []
        for root, dirs, files in os.walk(download_dir):
            for file in files:
                all_downloads.append(os.path.join(root, file))
        print(f"All files found: {all_downloads}")
        
        sys.exit(1)

except Exception as e:
    print(f"\n❌ Critical error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

finally:
    driver.quit()
    print("👋 Done")
