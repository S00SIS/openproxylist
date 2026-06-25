from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import sys

# ==================== Configuration ====================
options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

print("🚀 Launching ChromeDriver...")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
})

try:
    print("⏳ Opening website...")
    driver.get("https://openproxylist.com/v2ray/")
    
    # Wait for Cloudflare
    print("⏳ Waiting 60 seconds...")
    time.sleep(60)
    
    print(f"\n📄 Title: {driver.title}")
    print(f"🔗 URL: {driver.current_url}")
    
    # Save full page source
    with open("page_source.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print("💾 Page source saved to page_source.html")
    
    # Save screenshot
    driver.save_screenshot("page_screenshot.png")
    print("📸 Screenshot saved to page_screenshot.png")
    
    # Look for ALL elements with IDs
    all_elements = driver.find_elements(By.XPATH, "//*[@id]")
    ids = [elem.get_attribute('id') for elem in all_elements if elem.get_attribute('id')]
    print(f"\n🔍 Elements with IDs ({len(ids)}):")
    for id in ids[:30]:
        print(f"   - {id}")
    
    # Look for buttons
    buttons = driver.find_elements(By.TAG_NAME, "button")
    print(f"\n🔘 Buttons ({len(buttons)}):")
    for btn in buttons[:10]:
        try:
            print(f"   - ID: {btn.get_attribute('id')}, Text: {btn.text[:50]}")
        except:
            pass
    
    # Look for all links
    links = driver.find_elements(By.TAG_NAME, "a")
    print(f"\n🔗 Links ({len(links)}):")
    for link in links[:20]:
        try:
            href = link.get_attribute('href') or ''
            text = link.text[:50]
            if 'download' in href.lower() or 'next' in text.lower() or 'select' in text.lower():
                print(f"   - Text: {text}, Href: {href[:100]}")
        except:
            pass
    
    # Check if select-all exists
    try:
        select_all = driver.find_element(By.ID, "select-all")
        print(f"\n✅ select-all found! Displayed: {select_all.is_displayed()}")
    except:
        print("\n❌ select-all NOT found")
    
    # Check if bulk-download exists
    try:
        bulk_download = driver.find_element(By.ID, "bulk-download")
        print(f"✅ bulk-download found! Displayed: {bulk_download.is_displayed()}")
    except:
        print("❌ bulk-download NOT found")
    
    # Look for table
    try:
        table = driver.find_element(By.TAG_NAME, "table")
        print(f"\n✅ Table found!")
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        print(f"   Rows: {len(rows)}")
        if rows:
            print(f"   First row text: {rows[0].text[:100]}")
    except:
        print("\n❌ No table found")
    
    print("\n✅ Debug info collected")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()

# Upload artifact files
print("\n📤 Upload these files as artifacts to see what's happening:")
print("   - page_source.html")
print("   - page_screenshot.png")
