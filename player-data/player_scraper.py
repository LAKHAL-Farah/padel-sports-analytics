import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
from datetime import datetime

# Set headers to avoid blocking
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def calculate_age(date_of_birth):
    """Calculate age from date of birth"""
    try:
        dob = datetime.strptime(date_of_birth.strip(), "%d/%m/%Y")
        today = datetime.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age
    except:
        return None

def scrape_player_profile(player_url):
    """Scrape individual player profile data"""
    try:
        response = requests.get(player_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        player_data = {}
        full_text = soup.get_text()
        
        # Extract name - try h2 first, then h1, then from URL
        player_name = "Unknown"
        
        # Try h2 (primary heading on player page)
        h2_element = soup.find("h2")
        if h2_element:
            name_text = h2_element.text.strip()
            if name_text and name_text not in ["Back to Ranking", "MALE FIP RANKING", "Points breakdown by tournament", "TITLES AND FINALS"]:
                player_name = name_text
        
        # Fallback to h1 if h2 didn't work
        if player_name == "Unknown":
            h1_element = soup.find("h1")
            if h1_element:
                name_text = h1_element.text.strip()
                if name_text and name_text not in ["Back to Ranking", "MALE FIP RANKING"]:
                    player_name = name_text
        
        # Fallback to extracting from URL
        if player_name == "Unknown":
            player_name = player_url.split("/player/")[1].rstrip("/").replace("-", " ").title()
        
        player_data["name"] = player_name
        
        # Extract country
        country_code = "Unknown"
        country_img = soup.find("img", attrs={"alt": re.compile(r"^[A-Z]{3}$")})
        if country_img:
            country_code = country_img.get("alt", "Unknown")
        player_data["country"] = country_code
        
        # Extract image - find player's main image (not the country flag)
        player_img = ""
        for img in soup.find_all("img"):
            src = img.get("src", "")
            alt = img.get("alt", "")
            # Look for player images in uploads folder
            if "uploads" in src and src.endswith(".png") and "Fip" not in alt:
                player_img = src
                break
        
        player_data["image"] = player_img
        
        # Extract points
        points = "0"
        points_match = re.search(r"Points\s*(\d+)", full_text)
        if points_match:
            points = points_match.group(1)
        player_data["points"] = points
        
        # Extract personal information
        player_data["date_of_birth"] = "Unknown"
        player_data["age"] = "Unknown"
        dob_match = re.search(r"Date of birth\s*(\d{1,2}/\d{1,2}/\d{4})", full_text)
        if dob_match:
            dob = dob_match.group(1)
            player_data["date_of_birth"] = dob
            age = calculate_age(dob)
            if age:
                player_data["age"] = str(age)
        
        player_data["height"] = "Unknown"
        height_match = re.search(r"Height\s*([\d.]+)", full_text)
        if height_match:
            player_data["height"] = height_match.group(1)
        
        player_data["birthplace"] = "Unknown"
        born_match = re.search(r"Born in\s*([^•\n]+?)(?:Coach|Playing|$)", full_text)
        if born_match:
            place = born_match.group(1).strip()
            if place and len(place) < 100:
                player_data["birthplace"] = place
        
        player_data["playing_position"] = "Unknown"
        pos_match = re.search(r"Playing Position\s*(Left|Right)", full_text, re.IGNORECASE)
        if pos_match:
            player_data["playing_position"] = pos_match.group(1)
        
        player_data["coach"] = "Unknown"
        coach_match = re.search(r"Coach\s*([^•\n]+?)(?:Stats|$)", full_text)
        if coach_match:
            coach = coach_match.group(1).strip()
            if coach and len(coach) < 100 and "Stats" not in coach:
                player_data["coach"] = coach
        
        # Stats - N/A since they're loaded dynamically
        player_data["matches_played"] = "N/A"
        player_data["matches_won"] = "N/A"
        player_data["matches_lost"] = "N/A"
        player_data["consecutive_wins"] = "N/A"
        player_data["effectiveness"] = "N/A"
        player_data["titles"] = "N/A"
        player_data["best_rank"] = "N/A"
        
        player_data["gender"] = "Male"
        player_data["ranking"] = "Unknown"
        
        return player_data
        
    except Exception as e:
        print(f"  Error: {e}")
        return None

def scrape_ranking_page():
    """Scrape ranking page and get all players with ranking and points"""
    ranking_url = "https://www.padelfip.com/ranking-male/"
    
    try:
        response = requests.get(ranking_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        players = []
        seen_urls = set()
        
        # Find all player profile links
        for link in soup.find_all("a", href=re.compile(r"/player/[^/]+/$")):
            href = link.get("href")
            
            if href and href not in seen_urls:
                url_name = href.split("/player/")[1].rstrip("/").replace("-", " ").title()
                link_text = link.text.strip()
                player_name = link_text if link_text and link_text not in ["info"] else url_name
                
                # Get ranking position
                ranking = "Unknown"
                for prev_elem in link.find_all_previous(string=re.compile(r"^\d+\s*-?\s*$"), limit=10):
                    rank_text = prev_elem.strip().replace("-", "").strip()
                    if rank_text.isdigit():
                        ranking = rank_text
                        break
                
                # Get points
                points = "0"
                container = link.find_parent()
                if container:
                    container_text = container.get_text()
                    points_match = re.search(r"Points\s*(\d+)", container_text)
                    if points_match:
                        points = points_match.group(1)
                
                # Get image
                image_url = ""
                for img in link.find_all_next("img", limit=5):
                    src = img.get("src", "")
                    if src and "uploads" in src and "Fip" not in src:
                        image_url = src
                        break
                
                if player_name and href not in seen_urls:
                    players.append({
                        "url": href,
                        "name": player_name,
                        "ranking": ranking,
                        "points": points,
                        "image": image_url
                    })
                    seen_urls.add(href)
        
        return players
        
    except Exception as e:
        print(f"Error scraping ranking page: {e}")
        return []

def main():
    print("🏓 Scraping Padel FIP Player Data (Male Ranking)")
    print("=" * 60)
    
    ranking_players = scrape_ranking_page()
    
    if not ranking_players:
        print("❌ No players found")
        return
    
    print(f"✓ Found {len(ranking_players)} players\n")
    
    all_players = []
    
    for idx, player_info in enumerate(ranking_players, 1):
        print(f"[{idx:2d}/{len(ranking_players)}] {player_info['name']:<30} Rank: {player_info['ranking']:<5} Points: {player_info['points']:<6}", end=" ")
        
        profile = scrape_player_profile(player_info['url'])
        
        if profile:
            profile['ranking'] = player_info['ranking']
            profile['points'] = player_info['points']
            if player_info['image']:
                profile['image'] = player_info['image']
            
            all_players.append(profile)
            print("✓")
        else:
            print("✗")
        
        if idx % 5 == 0:
            time.sleep(1)
        else:
            time.sleep(0.2)
    
    if all_players:
        df = pd.DataFrame(all_players)
        
        columns_order = [
            "name", "country", "gender", "age", "date_of_birth",
            "height", "playing_position",
            "points", "image"
        ]
        
        columns_order = [col for col in columns_order if col in df.columns]
        df = df[columns_order]
        
        output_file = "padel_players_data.csv"
        df.to_csv(output_file, index=False)
        
        print("\n" + "=" * 60)
        print(f"✅ Data saved to: {output_file}")
        print(f"📊 Total players: {len(all_players)}")
        print(f"📈 Columns: {len(columns_order)}")
    else:
        print("\n❌ No data scraped")

if __name__ == "__main__":
    main()
