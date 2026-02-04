"""
Premier Padel Tournament Scraper using Selenium
This version can handle JavaScript-rendered content
Requires: pip install selenium webdriver-manager
"""

import pandas as pd
import re
import time
import json

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️ Selenium or webdriver-manager not installed.")
    print("Install with: pip install selenium webdriver-manager")

def scrape_tournaments_selenium():
    """Scrape tournament data using Selenium"""
    if not SELENIUM_AVAILABLE:
        return []
    
    tournaments_url = "https://premierpadel.com/en/tournaments"
    
    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    try:
        print(f"🌐 Starting Chrome browser...")
        # Use webdriver manager to automatically download and manage ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print(f"📡 Loading {tournaments_url}...")
        driver.get(tournaments_url)
        
        # Wait for page to load - give JavaScript time to render
        print("⏳ Waiting for tournaments to load...")
        time.sleep(8)  # Increased wait time for JavaScript rendering
        
        tournaments = []
        
        # Try multiple selectors to find tournament elements
        selectors = [
            "a[href*='tournaments']",
            "a[href*='tournament']",
            "div[class*='tournament']",
            "div[class*='card']"
        ]
        
        all_elements = []
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                all_elements.extend(elements)
            except:
                continue
        
        print(f"📋 Found {len(all_elements)} potential tournament elements")
        
        # Also try to find data in page source
        page_source = driver.page_source
        
        # Save page source for debugging
        with open("tournaments_selenium_page.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        print("💾 Saved page source to tournaments_selenium_page.html")
        
        # Try to extract tournament names and URLs from links
        seen_urls = set()
        for element in all_elements:
            try:
                # Get URL
                url = element.get_attribute("href")
                if not url or "tournament" not in url.lower() or url in seen_urls:
                    continue
                
                seen_urls.add(url)
                
                # Get text
                name = element.text.strip()
                if not name or len(name) < 3:
                    # Try finding nested elements
                    try:
                        h3 = element.find_element(By.TAG_NAME, "h3")
                        name = h3.text.strip()
                    except:
                        try:
                            h2 = element.find_element(By.TAG_NAME, "h2")
                            name = h2.text.strip()
                        except:
                            continue
                
                if not name or len(name) < 3:
                    continue
                
                # Extract category from name or URL
                category = "Unknown"
                for cat in ["MAJOR", "P1", "P2", "FINALS"]:
                    if cat in name.upper():
                        category = cat
                        break
                
                tournaments.append({
                    "tournament_name": name,
                    "category": category,
                    "url": url
                })
                
            except Exception as e:
                continue
        
        # Try scrolling to load more content
        print("📜 Scrolling to load all tournaments...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(5):  # Scroll 5 times
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        # Try again after scrolling
        more_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='tournament']")
        print(f"📋 After scrolling, found {len(more_links)} tournament links")
        
        for link in more_links:
            try:
                url = link.get_attribute("href")
                if not url or "tournament" not in url.lower() or url in seen_urls:
                    continue
                
                seen_urls.add(url)
                name = link.text.strip()
                
                if not name or len(name) < 3:
                    continue
                
                category = "Unknown"
                for cat in ["MAJOR", "P1", "P2", "FINALS"]:
                    if cat in name.upper():
                        category = cat
                        break
                
                tournaments.append({
                    "tournament_name": name,
                    "category": category,
                    "url": url
                })
            except:
                continue
        
        driver.quit()
        print(f"✓ Browser closed")
        
        # Remove duplicates based on tournament name
        seen_names = set()
        unique = []
        for t in tournaments:
            if t["tournament_name"] not in seen_names:
                seen_names.add(t["tournament_name"])
                unique.append(t)
        
        return unique
        
    except Exception as e:
        print(f"❌ Error: {e}")
        try:
            driver.quit()
        except:
            pass
        return []

def main():
    print("🏆 Scraping Premier Padel Tournaments (Selenium)")
    print("=" * 60)
    
    if not SELENIUM_AVAILABLE:
        print("\n📦 Selenium is required for this scraper")
        print("Install it with: pip install selenium webdriver-manager")
        print("\nAlternatively, use scrape_tournaments_manual.py for manual data entry")
        return
    
    tournaments = scrape_tournaments_selenium()
    
    if tournaments:
        # Add placeholder data for other fields
        for t in tournaments:
            if "dates" not in t:
                t["dates"] = "Unknown"
            if "venue" not in t:
                t["venue"] = "Unknown"
            if "location" not in t:
                t["location"] = "Unknown"
            if "prize_money" not in t:
                t["prize_money"] = "Unknown"
            if "status" not in t:
                t["status"] = "Unknown"
            if "image" not in t:
                t["image"] = ""
        
        df = pd.DataFrame(tournaments)
        output_file = "premier_padel_tournaments_selenium.csv"
        df.to_csv(output_file, index=False)
        
        print(f"\n✅ Data saved to: {output_file}")
        print(f"📊 Total tournaments: {len(tournaments)}")
        print(f"📋 Columns: {', '.join(df.columns)}")
        print("\nTournaments found:")
        for idx, t in enumerate(tournaments, 1):
            print(f"  {idx}. {t['tournament_name']} ({t['category']})")
    else:
        print("\n❌ No tournament data found")
        print("The site uses heavy JavaScript. You may need to:")
        print("  1. Check the saved HTML file: tournaments_selenium_page.html")
        print("  2. Use the manual template: scrape_tournaments_manual.py")
        print("  3. Visit the website and manually add tournament data")

if __name__ == "__main__":
    main()
