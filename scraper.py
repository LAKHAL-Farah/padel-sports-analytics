import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

# Step 1: URL of rankings
url = "https://www.padelfip.com/ranking-male/"

# Step 2: Download page with headers to avoid blocking
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}
response = requests.get(url, headers=headers)
if response.status_code != 200:
    print("Failed to load page")
    exit()

# Step 3: Parse HTML
soup = BeautifulSoup(response.text, "html.parser")

players = []

# Step 4: Find the ranking table
table = soup.find("table")
if table:
    rows = table.find_all("tr")
    for row in rows[1:]:  # skip header
        cols = row.find_all("td")
        if len(cols) >= 4:
            # Extract image URL
            img_tag = cols[1].find("img") if len(cols) > 1 else None
            image_url = img_tag.get("src") if img_tag else ""
            
            players.append({
                "rank": cols[0].text.strip(),
                "player": cols[1].text.strip(),
                "country": cols[2].text.strip(),
                "points": cols[3].text.strip(),
                "image": image_url
            })

# Step 5: If table parsing fails, try alternative method (parsing divs)
if not players:
    # Try scraping from div structure
    ranking_items = soup.find_all("div", class_=re.compile(r"ranking|player", re.IGNORECASE))
    
    # Look for specific data patterns
    for item in soup.find_all("tr"):
        cols = item.find_all("td")
        if len(cols) >= 4:
            rank_text = cols[0].text.strip()
            player_text = cols[1].text.strip()
            country_text = cols[2].text.strip()
            points_text = cols[3].text.strip()
            
            # Extract image URL
            img_tag = cols[1].find("img") if len(cols) > 1 else None
            image_url = img_tag.get("src") if img_tag else ""
            
            # Only add if we have valid data
            if rank_text and player_text and country_text and points_text:
                players.append({
                    "rank": rank_text,
                    "player": player_text,
                    "country": country_text,
                    "points": points_text,
                    "image": image_url
                })

# Step 6: Save as CSV
if players:
    df = pd.DataFrame(players)
    df.to_csv("padel_rankings.csv", index=False)
    print(f"✅ Data saved to padel_rankings.csv ({len(players)} players found)")
else:
    print("⚠️ No data found. The website structure may have changed.")
