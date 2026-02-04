import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

# Set headers to avoid blocking
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def scrape_male_ranking():
    """Scrape male ranking table from padelfip.com"""
    ranking_url = "https://www.padelfip.com/ranking-male/"
    
    try:
        response = requests.get(ranking_url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Failed to load page (Status: {response.status_code})")
            return []
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        players = []
        
        # Find the ranking table
        table = soup.find("table")
        if table:
            rows = table.find_all("tr")
            for row in rows[1:]:  # Skip header
                cols = row.find_all("td")
                if len(cols) >= 3:
                    rank = cols[0].text.strip()
                    player = cols[1].text.strip()
                    country = cols[2].text.strip()
                    points = cols[3].text.strip() if len(cols) > 3 else "0"
                    
                    # Extract image URL if available
                    img = cols[1].find("img") if len(cols) > 1 else None
                    image_url = img.get("src", "") if img else ""
                    
                    players.append({
                        "rank": rank,
                        "player": player,
                        "country": country,
                        "points": points,
                        "image": image_url
                    })
        
        # If table parsing fails, try alternative method (parsing divs)
        if not players:
            # Look for player links and extract data from structure
            for link in soup.find_all("a", href=re.compile(r"/player/[^/]+/$")):
                # Get container
                container = link.find_parent()
                if container:
                    text = container.get_text()
                    
                    # Extract rank
                    rank_match = re.search(r"^\s*(\d+)\s*", text)
                    rank = rank_match.group(1) if rank_match else "Unknown"
                    
                    # Extract player name
                    player_name = link.text.strip()
                    
                    # Extract country
                    country_img = container.find("img", attrs={"alt": re.compile(r"^[A-Z]{3}$")})
                    country = country_img.get("alt", "Unknown") if country_img else "Unknown"
                    
                    # Extract points
                    points_match = re.search(r"Points\s*(\d+)", text)
                    points = points_match.group(1) if points_match else "0"
                    
                    # Extract image
                    img = link.find_next("img")
                    image_url = ""
                    if img:
                        src = img.get("src", "")
                        if "uploads" in src:
                            image_url = src
                    
                    if player_name and rank != "Unknown":
                        players.append({
                            "rank": rank,
                            "player": player_name,
                            "country": country,
                            "points": points,
                            "image": image_url
                        })
        
        # Remove duplicates based on player name
        seen = set()
        unique_players = []
        for p in players:
            if p["player"] not in seen:
                seen.add(p["player"])
                unique_players.append(p)
        
        return unique_players
        
    except Exception as e:
        print(f"Error scraping ranking page: {e}")
        return []

def main():
    print("🏓 Scraping Padel FIP Male Ranking")
    print("=" * 60)
    
    players = scrape_male_ranking()
    
    if players:
        df = pd.DataFrame(players)
        
        output_file = "male_ranking.csv"
        df.to_csv(output_file, index=False)
        
        print(f"✅ Data saved to: {output_file}")
        print(f"📊 Total players: {len(players)}")
        print(f"📋 Columns: {', '.join(df.columns)}")
    else:
        print("❌ No ranking data found")

if __name__ == "__main__":
    main()
