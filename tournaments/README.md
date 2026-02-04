# Premier Padel Tournament Data

This folder contains scripts to extract tournament data from https://premierpadel.com/en/tournaments

## Important Note

The Premier Padel website uses JavaScript (Next.js) to render content dynamically, which means simple HTML scraping won't work. There are three approaches:

### Option 1: Manual Data Entry (Recommended for now)
Use `scrape_tournaments_manual.py` - Add tournament data manually from the website.

**Run:**
```bash
python scrape_tournaments_manual.py
```

### Option 2: Selenium Scraper (For Automated JS Scraping)
Use `scrape_tournaments_selenium.py` - Requires Selenium and ChromeDriver.

**Install Selenium:**
```bash
pip install selenium
```

**Run:**
```bash
python scrape_tournaments_selenium.py
```

### Option 3: API Approach
If Premier Padel has a public API, that would be the best solution.

## Data Fields

The tournament CSV includes:
- `tournament_name`: Name of the tournament
- `category`: P1, P2, MAJOR, or FINALS
- `dates`: Tournament dates
- `venue`: Stadium/venue name
- `location`: City and country
- `prize_money`: Prize pool
- `status`: Upcoming, Live, or Completed
- `url`: Tournament page URL
- `tickets_url`: Where to buy tickets (if available)
- `image`: Tournament promotional image

## Current Data

Based on February 2026, visible tournaments include:
- **RIYADH SEASON P1** (07-14 February 2026, Padel Rush Arena)

Visit https://premierpadel.com/en/tournaments to see the full tournament calendar.
