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

driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
})
driver.execute_cdp_cmd("Page.setDownloadBehavior", {
    "behavior": "allow",
    "downloadPath": download_dir
})

wait = WebDriverWait(driver, 120)

try:
    print("⏳ Opening website...")
    driver.get("https://openproxylist.com/v2ray/")
    
    print("⏳ Waiting 60 seconds for page to fully load...")
    time.sleep(60)
    
    page = 1
    
    while True:
        print(f"\n{'='*50}")
        print(f"📄 Processing page {page}")
        print(f"{'='*50}")
        
        # Wait 60 seconds for elements to appear
        print("⏳ Waiting 60 seconds for Select All to appear...")
        time.sleep(60)
        
        # Click Select All
        try:
            select_all = wait.until(EC.element_to_be_clickable((By.ID, "select-all")))
            driver.execute_script("arguments[0].click();", select_all)
            print("✅ Select All clicked")
        except Exception as e:
            print(f"❌ Select All failed: {str(e)[:100]}")
            break
        
        time.sleep(5)
        
        # Click Bulk Download
        try:
            bulk_download = wait.until(EC.element_to_be_clickable((By.ID, "bulk-download")))
            driver.execute_script("arguments[0].click();", bulk_download)
            print("✅ Bulk Download clicked")
        except Exception as e:
            print(f"❌ Bulk Download failed: {str(e)[:100]}")
            break
        
        print("⏳ Waiting 30 seconds for download...")
        time.sleep(30)
        
        # Click Next
        try:
            next_btn = None
            next_selectors = [
                "//a[contains(text(), 'Next')]",
                "//button[contains(text(), 'Next')]",
                "//span[contains(text(), 'Next')]",
            ]
            
            for selector in next_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            if "disabled" not in (elem.get_attribute("class") or ""):
                                next_btn = elem
                                break
                    if next_btn:
                        break
                except:
                    continue
            
            if next_btn:
                driver.execute_script("arguments[0].click();", next_btn)
                print(f"➡️ Moving to page {page + 1}")
                page += 1
                time.sleep(10)
            else:
                print("🛑 No more pages")
                break
                
        except Exception as e:
            print(f"🛑 Next failed: {str(e)[:100]}")
            break

    # Merge files
    print(f"\n{'='*50}")
    print("🔍 Merging files...")
    time.sleep(10)
    
    txt_files = sorted(glob.glob(os.path.join(download_dir, "*.txt")))
    print(f"📁 Found {len(txt_files)} files")
    
    if txt_files:
        merged_file = os.path.join(os.getcwd(), "ALL_V2RAY_CONFIGS.txt")
        total = 0
        
        with open(merged_file, "w", encoding="utf-8") as outfile:
            for i, f in enumerate(txt_files):
                with open(f, "r", encoding="utf-8") as infile:
                    content = infile.read().strip()
                    if content:
                        lines = content.split('\n')
                        total += len(lines)
                        outfile.write(content)
                        if i < len(txt_files) - 1:
                            outfile.write("\n")
                print(f"   ✅ {os.path.basename(f)} merged")
        
        print(f"\n🎉 Done! {total} configs saved to ALL_V2RAY_CONFIGS.txt")
        print(f"📏 Size: {os.path.getsize(merged_file)} bytes")
        sys.exit(0)
    else:
        print("❌ No files found!")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

finally:
    driver.quit()
    print("👋 Done")
