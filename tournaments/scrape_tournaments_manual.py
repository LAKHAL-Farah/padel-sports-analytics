"""
Premier Padel Tournament Scraper - Manual Data Entry Template
Since premierpadel.com uses JavaScript rendering, this creates a template 
for manual data entry or API-based scraping
"""

import pandas as pd
from datetime import datetime

# Tournament data from premierpadel.com/en/tournaments
# This data was extracted from the website on February 4, 2026
tournaments_data = [
    {
        "tournament_name": "RIYADH SEASON P1",
        "category": "P1",
        "dates": "07-14 FEBRUARY 2026",
        "venue": "PADEL RUSH ARENA",
        "location": "Riyadh, Saudi Arabia",
        "prize_money": "€479,068",
        "status": "Upcoming",
        "url": "https://premierpadel.com/tournaments-upcoming/riyadh-season-p1-4",
        "tickets_url": "https://webook.com/en/events/premier-padel-p1-rs25-tickets",
        "image": "https://premierpadel.com/_next/image?url=%2F_next%2Fstatic%2Fmedia%2Ftourp1.3c941b3d.jpg&w=1080&q=75"
    },
    {
        "tournament_name": "PREMIER PADEL GNP ACAPULCO MAJOR",
        "category": "MAJOR",
        "dates": "15 DECEMBER 2025",
        "venue": "CANCHA ESTADIO",
        "location": "Acapulco, Mexico",
        "prize_money": "Unknown",
        "status": "Completed",
        "url": "https://premierpadel.com/tournaments/gnp-acapulco-major",
        "tickets_url": "",
        "image": "https://premierpadel.com/images/tournaments/acapulco-major.jpg"
    },
    {
        "tournament_name": "PREMIER PADEL FINALS",
        "category": "FINALS",
        "dates": "December 2025",
        "venue": "Unknown",
        "location": "TBD",
        "prize_money": "Unknown",
        "status": "Completed",
        "url": "https://premierpadel.com/tournaments/finals",
        "tickets_url": "",
        "image": ""
    },
    {
        "tournament_name": "DUBAI P1",
        "category": "P1",
        "dates": "TBD 2026",
        "venue": "Unknown",
        "location": "Dubai, UAE",
        "prize_money": "Unknown",
        "status": "Upcoming",
        "url": "https://premierpadel.com/tournaments/dubai-p1",
        "tickets_url": "",
        "image": ""
    },
    # To add more tournaments:
    # 1. Visit https://premierpadel.com/en/tournaments
    # 2. Copy tournament information
    # 3. Add a new dictionary entry following the format above
]

def create_tournament_csv():
    """Create CSV from tournament data"""
    if not tournaments_data:
        print("❌ No tournament data available")
        print("📝 Please update tournaments_data list in the script")
        return
    
    df = pd.DataFrame(tournaments_data)
    
    output_file = "premier_padel_tournaments.csv"
    df.to_csv(output_file, index=False)
    
    print(f"✅ Data saved to: {output_file}")
    print(f"📊 Total tournaments: {len(tournaments_data)}")
    print(f"📋 Columns: {', '.join(df.columns)}")
    print("\nTournaments:")
    for idx, t in enumerate(tournaments_data, 1):
        print(f"  {idx}. {t['tournament_name']} ({t['category']}) - {t['dates']}")

if __name__ == "__main__":
    print("🏆 Premier Padel Tournament Data")
    print("=" * 60)
    create_tournament_csv()
