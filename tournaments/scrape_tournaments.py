import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time

# Set headers to avoid blocking
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def scrape_tournaments():
    """Scrape tournament data from Premier Padel website"""
    base_url = "https://premierpadel.com"
    tournaments_url = "https://premierpadel.com/en/tournaments"
    
    try:
        print(f"Fetching tournament data from {tournaments_url}...")
        response = requests.get(tournaments_url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"Failed to load page (Status: {response.status_code})")
            return []
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Save HTML for debugging
        with open("tournaments_page.html", "w", encoding="utf-8") as f:
            f.write(soup.prettify())
        print("Saved HTML to tournaments_page.html for inspection")
        
        tournaments = []
        
        # Look for tournament links (tournaments-upcoming or tournaments/)
        tournament_links = soup.find_all("a", href=re.compile(r"/(tournaments-upcoming|tournaments)/"))
        
        print(f"Found {len(tournament_links)} tournament links")
        
        for link in tournament_links:
            tournament_url = link.get("href")
            if not tournament_url.startswith("http"):
                tournament_url = base_url + tournament_url
            
            # Extract tournament name from link text
            tournament_name = link.get_text(strip=True)
            if not tournament_name or len(tournament_name) < 3:
                # Try finding h3 or h2 in link
                heading = link.find(['h3', 'h2', 'h4'])
                if heading:
                    tournament_name = heading.get_text(strip=True)
            
            if not tournament_name or len(tournament_name) < 3:
                continue
            
            # Find the parent container for more details
            container = link.find_parent()
            for _ in range(5):  # Go up a few levels to find the card/section
                if container:
                    container = container.find_parent()
                else:
                    break
            
            if not container:
                container = link.find_parent()
            
            # Extract data from container
            text = container.get_text() if container else ""
            
            # Extract dates (e.g., "07-14 FEBRUARY")
            dates = "Unknown"
            date_patterns = [
                r"(\d{1,2}-\d{1,2}\s+[A-Z]+)",
                r"(\d{1,2}/\d{1,2}/\d{4})",
                r"(\d{1,2}\s+[A-Z]+\s+\d{4})"
            ]
            for pattern in date_patterns:
                date_match = re.search(pattern, text)
                if date_match:
                    dates = date_match.group(1)
                    break
            
            # Extract venue
            venue = "Unknown"
            venue_match = re.search(r"Venue([^\n]+)", text, re.IGNORECASE)
            if venue_match:
                venue = venue_match.group(1).strip()
            
            # Extract prize money
            prize_money = "Unknown"
            prize_match = re.search(r"Prize Money[€$£]([\d,]+)", text)
            if prize_match:
                prize_money = "€" + prize_match.group(1)
            
            # Extract category (P1, P2, MAJOR, etc.)
            category = "Unknown"
            for cat in ["MAJOR", "P1", "P2", "FINALS"]:
                if cat in tournament_name.upper() or cat in text.upper():
                    category = cat
                    break
            
            # Extract status
            status = "Upcoming"
            if "COMPLETED" in text.upper():
                status = "Completed"
            elif "LIVE" in text.upper():
                status = "Live"
            
            # Extract image
            image_url = ""
            img = container.find("img") if container else None
            if img:
                src = img.get("src", "")
                if src:
                    if not src.startswith("http"):
                        if src.startswith("/"):
                            image_url = base_url + src
                        else:
                            image_url = src
                    else:
                        image_url = src
            
            tournaments.append({
                "tournament_name": tournament_name,
                "category": category,
                "dates": dates,
                "venue": venue,
                "prize_money": prize_money,
                "status": status,
                "url": tournament_url,
                "image": image_url
            })
        
        # Remove duplicates based on tournament name
        seen = set()
        unique_tournaments = []
        for t in tournaments:
            key = t["tournament_name"]
            if key not in seen:
                seen.add(key)
                unique_tournaments.append(t)
        
        return unique_tournaments
        
    except Exception as e:
        print(f"Error scraping tournaments: {e}")
        return []

def scrape_tournament_details(tournament_url):
    """Scrape detailed information from a specific tournament page"""
    try:
        response = requests.get(tournament_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return {}
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        details = {
            "category": "Unknown",
            "prize_money": "Unknown",
            "surface": "Unknown",
            "venue": "Unknown"
        }
        
        # Extract details from page
        text = soup.get_text()
        
        # Category
        for category in ["P1", "P2", "MAJOR", "FINALS"]:
            if category in text.upper():
                details["category"] = category
                break
        
        # Venue
        venue_match = re.search(r"Venue[:\s]+([^\n]+)", text, re.IGNORECASE)
        if venue_match:
            details["venue"] = venue_match.group(1).strip()
        
        # Prize money
        prize_match = re.search(r"([\$€£]\s*[\d,]+)", text)
        if prize_match:
            details["prize_money"] = prize_match.group(1)
        
        return details
        
    except Exception as e:
        print(f"Error scraping tournament details: {e}")
        return {}

def main():
    print("🏆 Scraping Premier Padel Tournament Data")
    print("=" * 60)
    
    tournaments = scrape_tournaments()
    
    if tournaments:
        print(f"✓ Found {len(tournaments)} tournaments\n")
        
        # Optionally, fetch detailed info for each tournament
        # (Commented out to avoid excessive requests)
        # for idx, tournament in enumerate(tournaments, 1):
        #     print(f"[{idx}/{len(tournaments)}] Fetching details for {tournament['tournament_name']}...")
        #     details = scrape_tournament_details(tournament['url'])
        #     tournament.update(details)
        #     time.sleep(1)  # Be polite
        
        df = pd.DataFrame(tournaments)
        
        output_file = "premier_padel_tournaments.csv"
        df.to_csv(output_file, index=False)
        
        print(f"✅ Data saved to: {output_file}")
        print(f"📊 Total tournaments: {len(tournaments)}")
        print(f"📋 Columns: {', '.join(df.columns)}")
    else:
        print("❌ No tournament data found")

if __name__ == "__main__":
    main()
