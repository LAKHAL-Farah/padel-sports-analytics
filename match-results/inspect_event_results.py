import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

EVENT_URL = "https://www.padelfip.com/events/fip-bronze-mallorca-2026/"

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    driver.get(EVENT_URL)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    time.sleep(3)

    # Click Results tab
    try:
        results_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Results')] | //button[contains(., 'Results')]"))
        )
        driver.execute_script("arguments[0].click();", results_tab)
        time.sleep(3)
    except Exception as e:
        print(f"Could not click Results tab: {e}")

    html = driver.page_source
    with open("event_results_page.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Saved event_results_page.html")
finally:
    driver.quit()
