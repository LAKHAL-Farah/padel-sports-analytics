"""
Comprehensive Premier Padel Tournament Scraper
Extracts ALL tournaments by parsing the rendered HTML
"""

import pandas as pd
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

def scrape_all_tournaments():
    """Scrape all tournaments across all months/years"""
    
    base_url = "https://premierpadel.com"
    tournaments_url = f"{base_url}/en/tournaments"
    
    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    try:
        print("🌐 Starting browser...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        all_tournaments = []

        def extract_tournaments_from_page(current_month, current_year):
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            tournament_cards = soup.find_all('div', class_=re.compile(r'matchcard-box'))
            if tournament_cards:
                print(f"    Found {len(tournament_cards)} tournament(s)")
            for card in tournament_cards:
                try:
                    name_elem = card.find('a', href=re.compile(r'/tournaments'))
                    if not name_elem:
                        continue

                    name = name_elem.get('title', '').strip() or name_elem.text.strip()
                    url = base_url + name_elem.get('href', '')

                    date_elem = card.find('h4')
                    dates = date_elem.text.strip() if date_elem else "Unknown"
                    if current_year and dates != "Unknown" and str(current_year) not in dates:
                        dates = f"{dates} {current_year}"

                    venue_elem = card.find('strong', string=re.compile(r'ARENA|CLUB|STADIUM|HALL', re.I))
                    if not venue_elem:
                        venue_span = card.find(string=re.compile(r'Venue', re.I))
                        if venue_span:
                            venue_elem = venue_span.find_next('strong')
                    venue = venue_elem.text.strip() if venue_elem else "Unknown"

                    prize_elem = card.find('strong', string=re.compile(r'€[\d,]+'))
                    if not prize_elem:
                        prize_text = card.find(string=re.compile(r'€[\d,]+'))
                        prize = prize_text.strip() if prize_text else "Unknown"
                    else:
                        prize = prize_elem.text.strip()

                    status_elem = card.find('div', string=re.compile(r'Upcoming|Completed|Live', re.I))
                    status = status_elem.text.strip() if status_elem else "Unknown"

                    category = "Unknown"
                    classes = ' '.join(card.get('class', []))
                    for cat in ["MAJOR", "P1", "P2", "FINALS"]:
                        if cat in classes or cat in name.upper():
                            category = cat
                            break

                    image_url = ""
                    img = card.find('img', alt="bg")
                    if img and img.get('srcset'):
                        srcset = img.get('srcset', '')
                        matches = re.findall(r'(/_next/image[^\s]+)\s+\d+w', srcset)
                        if matches:
                            image_url = base_url + matches[-1]

                    tournament = {
                        "tournament_name": name.title(),
                        "category": category,
                        "dates": dates,
                        "venue": venue,
                        "prize_money": prize,
                        "status": status,
                        "url": url,
                        "image": image_url,
                        "month": current_month,
                        "year": current_year
                    }

                    if not any(t['url'] == url for t in all_tournaments):
                        all_tournaments.append(tournament)
                        print(f"      ✓ {name}")
                except Exception as e:
                    print(f"      ✗ Error extracting tournament: {e}")

        years = [2025, 2026]

        def select_year(target_year):
            try:
                dropdown = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".react-dropdown-select"))
                )
                driver.execute_script("arguments[0].click();", dropdown)
                time.sleep(1)

                option_xpath = (
                    f"//div[contains(@class,'react-dropdown-select-item') and normalize-space()='{target_year}']"
                    f"|//span[normalize-space()='{target_year}']"
                )
                year_option = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, option_xpath))
                )
                driver.execute_script("arguments[0].click();", year_option)
                time.sleep(2)
                return True
            except Exception as e:
                print(f"  ⚠️ Could not select year {target_year}: {e}")
                return False

        def get_months_list():
            month_elements = driver.find_elements(By.CSS_SELECTOR, ".swiper-slide span.cursor-pointer")
            months = [el.text.strip() for el in month_elements if el.text.strip()]
            return list(dict.fromkeys(months))

        def click_next_month_arrow():
            try:
                arrow = driver.find_element(
                    By.XPATH,
                    "//button[.//img[contains(@src,'rarrow.svg')]]"
                )
                driver.execute_script("arguments[0].click();", arrow)
                time.sleep(1)
                return True
            except Exception:
                return False

        driver.get(tournaments_url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".tournaments-page"))
        )

        for year in years:
            print(f"\n📅 Checking year {year}...")
            select_year(year)

            seen_months = set()
            no_new_months_rounds = 0
            max_rounds = 24

            for _ in range(max_rounds):
                months = get_months_list()
                new_months = [m for m in months if m not in seen_months]

                if not new_months:
                    no_new_months_rounds += 1
                else:
                    no_new_months_rounds = 0

                for month in new_months:
                    try:
                        print(f"  ➤ {month} {year}...")
                        month_xpath = f"//span[normalize-space()='{month}' and contains(@class,'cursor-pointer')]"
                        month_el = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, month_xpath))
                        )
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", month_el)
                        driver.execute_script("arguments[0].click();", month_el)
                        time.sleep(2)

                        extract_tournaments_from_page(month, year)
                        seen_months.add(month)
                    except Exception as e:
                        print(f"    ✗ Error checking {month}: {e}")
                        continue

                if no_new_months_rounds >= 2:
                    break

                if not click_next_month_arrow():
                    break
        
        driver.quit()
        print("\n✓ Browser closed")
        
        return all_tournaments
        
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        try:
            driver.quit()
        except:
            pass
        return []

def main():
    print("🏆 Comprehensive Premier Padel Tournament Scraper")
    print("=" * 60)
    
    tournaments = scrape_all_tournaments()
    
    if tournaments:
        # Add location field (extract from venue or set as Unknown)
        for t in tournaments:
            if "location" not in t:
                t["location"] = "Unknown"
        
        df = pd.DataFrame(tournaments)
        output_file = "premier_padel_tournaments_complete.csv"
        df.to_csv(output_file, index=False)
        
        print(f"\n✅ Data saved to: {output_file}")
        print(f"📊 Total tournaments: {len(tournaments)}")
        print(f"📋 Columns: {', '.join(df.columns)}")
        
        print("\n🎾 Tournaments by Category:")
        category_counts = df['category'].value_counts()
        for cat, count in category_counts.items():
            print(f"  {cat}: {count}")
        
        print("\n📋 All tournaments:")
        for idx, t in enumerate(tournaments, 1):
            print(f"  {idx}. {t['tournament_name']} ({t['category']}) - {t['dates']}")
    else:
        print("\n❌ No tournaments found")
        print("Check the Selenium output above for errors")

if __name__ == "__main__":
    main()
