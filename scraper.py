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
options.add_argument("--headless=new")  # Headless mode for GitHub Actions
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
wait = WebDriverWait(driver, 60)

try:
    print("⏳ Opening website...")
    driver.get("https://openproxylist.com/v2ray/")
    
    # ====== 40 seconds wait for site to fully load ======
    print("⏳ Waiting 40 seconds for site to fully load...")
    for i in range(40, 0, -1):
        print(f"   {i} seconds remaining...", end="\r")
        time.sleep(1)
    print("\n✅ 40 seconds wait completed!")
    
    page = 1
    while True:
        print(f"\n{'='*50}")
        print(f"📄 Processing page {page}")
        print(f"{'='*50}")

        print("⏳ Waiting 15 seconds for page to fully load...")
        time.sleep(15)
        print("✅ Wait completed. Starting operations...")
        
        # ====== Select All ======
        try:
            print("🔍 Looking for Select All button...")
            select_all = wait.until(
                EC.element_to_be_clickable((By.ID, "select-all"))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", select_all)
            
            print("⏳ Waiting 15 seconds before clicking Select All...")
            time.sleep(15)
            
            select_all.click()
            print("✅ Select All clicked successfully")
        except Exception as e:
            print(f"❌ Error with Select All: {e}")
            try:
                driver.execute_script("document.getElementById('select-all').click();")
                print("✅ Select All clicked via JavaScript")
            except Exception as e2:
                print(f"❌ Second error with Select All: {e2}")
                break
        
        print("⏳ Waiting 15 seconds after Select All...")
        time.sleep(15)
        
        # ====== Bulk Download ======
        try:
            print("🔍 Looking for Bulk Download button...")
            bulk_download = wait.until(
                EC.element_to_be_clickable((By.ID, "bulk-download"))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", bulk_download)
            
            print("⏳ Waiting 15 seconds before clicking Bulk Download...")
            time.sleep(15)
            
            bulk_download.click()
            print("✅ Download started successfully")
        except Exception as e:
            print(f"❌ Error with Bulk Download: {e}")
            try:
                driver.execute_script("document.getElementById('bulk-download').click();")
                print("✅ Bulk Download clicked via JavaScript")
            except Exception as e2:
                print(f"❌ Second error with Bulk Download: {e2}")
                break
        
        print("⏳ Waiting 20 seconds for download to complete...")
        time.sleep(20)
        
        # ====== Next Page ======
        try:
            print("🔍 Looking for Next button...")
            next_found = False
            next_selectors = [
                "//a[contains(text(), 'Next')]",
                "//button[contains(text(), 'Next')]",
                "//span[contains(text(), 'Next')]",
                "//li[contains(@class, 'next')]//a",
                "//*[@id='next-page']",
                "//a[contains(@aria-label, 'Next')]",
            ]
            
            for selector in next_selectors:
                try:
                    next_buttons = driver.find_elements(By.XPATH, selector)
                    for btn in next_buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            class_attr = btn.get_attribute("class") or ""
                            if "disabled" not in class_attr:
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                
                                print("⏳ Waiting 15 seconds before clicking Next...")
                                time.sleep(15)
                                
                                btn.click()
                                print(f"✅ Next found and clicked using {selector}")
                                next_found = True
                                break
                    if next_found:
                        break
                except:
                    continue
            
            if next_found:
                print(f"➡️ Moving to page {page + 1}")
                print("⏳ Waiting 15 seconds for new page to load...")
                time.sleep(15)
                page += 1
            else:
                print("🛑 Active Next button not found - reached the last page")
                break
                
        except Exception as e:
            print(f"🛑 Error with Next or last page reached: {e}")
            break

    print("\n" + "="*50)
    print("✅ All pages downloaded successfully!")
    print("="*50)

    # ==================== Merge Files ====================
    print("\n🔍 Searching for downloaded files...")
    time.sleep(5)
    
    txt_files = sorted(glob.glob(os.path.join(download_dir, "*.txt")))
    print(f"📁 Number of txt files found: {len(txt_files)}")
    
    if txt_files:
        for f in txt_files:
            size = os.path.getsize(f)
            print(f"   📄 {os.path.basename(f)} - {size} bytes")
        
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
                print(f"   ✅ {os.path.basename(file)} merged successfully")

        print(f"\n{'='*50}")
        print(f"🎉 Operation completed successfully!")
        print(f"📊 Total configs count: {total_configs}")
        print(f"📁 Final file: {merged_file}")
        print(f"{'='*50}")
        
        # Verify the output file exists
        if os.path.exists(merged_file):
            final_size = os.path.getsize(merged_file)
            print(f"✅ Output file verified: {final_size} bytes")
        else:
            print("❌ Output file not found!")
            sys.exit(1)
    else:
        print("⚠️ No txt files found!")
        print("Download folder contents:")
        for f in os.listdir(download_dir):
            print(f"   - {f}")
        sys.exit(1)

except Exception as e:
    print("\n" + "="*50)
    print("❌ Critical error occurred:")
    print("="*50)
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {e}")
    print("\nFull Traceback:")
    import traceback
    traceback.print_exc()
    print("="*50)
    sys.exit(1)

finally:
    driver.quit()
    print("👋 Browser closed")
