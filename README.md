# 🎾 BI Padel - Padel Tournament Data Analytics

Comprehensive web scraping and BI analytics platform for padel tournament data from **padelfip.com**, **premierpadel.com**, and social media sources.

## 🎯 Project Overview

This project collects and enriches padel tournament and player data through automated web scraping, preparing it for business intelligence analysis and forecasting.

**Main Achievement:** Built production-grade web scrapers that collect 692+ tournaments and 13,000+ match results with zero API keys required.

## 📊 What Gets Scraped

### Tournament Data (padelfip.com)
- **Tournament calendar** - 692 events across 2025-2026
- **Match results** - 13,441 matches with scores, courts, rounds
- **Venue information** - Addresses, court counts, indoor/outdoor indicators
- **Status tracking** - Registration status, finished/live events

### Premier Padel Data (premierpadel.com)
- Tournament list with categories (P1, P2, Majors, Finals)
- Prize money, venues, dates, registration status

### Social Media (Framework)
- YouTube channel and video metrics (no API key needed)
- Instagram/Twitter/Facebook templates for manual collection
- Engagement metrics and follower tracking

## 📁 Project Structure

```
BI padel/
├── match-results/              # FIP tournament scraping
│   ├── scrape_padelfip_calendar_and_results.py
│   ├── padelfip_tournaments.csv       (692 tournaments)
│   └── match_results.csv              (13,441 matches)
│
├── courts-and-venues/          # Venue & court data
│   ├── scrape_venues_and_courts.py
│   └── venues_and_courts.csv
│
├── bi-analytics/               # BI-focused enrichment
│   ├── add_time_dimensions.py
│   ├── tournaments_with_time_dimensions.csv
│   ├── match_results_with_time_dimensions.csv
│   └── time_dimension_analysis.txt
│
├── tournaments/                # Premier Padel & compiled data
│   └── premier_padel_tournaments_complete.csv
│
├── social-media/               # Social media scrapers
│   ├── youtube_scraper.py
│   ├── youtube_scraper_no_api.py
│   └── social_media_scraper.py
│
├── player-data/                # Player information
├── rankings/                   # Rankings data
└── venv/                       # Python virtual environment
```

## 🚀 Quick Start

### 1. Setup

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies (if needed)
pip install requests beautifulsoup4 pandas selenium webdriver-manager
```

### 2. Scrape Tournament Data

```bash
# Scrape 2025-2026 tournaments and match results
python match-results/scrape_padelfip_calendar_and_results.py --years 2026 2025

# Output: padelfip_tournaments.csv (692 tournaments)
#         match_results.csv (13,441 matches)
```

### 3. Scrape Venue Data

```bash
# Extract venue information
python courts-and-venues/scrape_venues_and_courts.py --years 2026 2025

# Output: venues_and_courts.csv (692 venues)
```

### 4. Add BI Dimensions

```bash
# Enrich with time dimensions for analysis
python bi-analytics/add_time_dimensions.py

# Output: tournaments_with_time_dimensions.csv (with Year, Month, Season, etc.)
#         match_results_with_time_dimensions.csv
#         time_dimension_analysis.txt
```

## 📈 Key Data Insights

### Growth Analysis
- **2025**: 294 tournaments
- **2026**: 398 tournaments
- **Growth**: +35.4% YoY

### Tournament Distribution
- **Spring**: 225 tournaments (peak season)
- **Peak month**: April (90 tournaments)
- **Lowest**: December (7 - holidays)

### Match Data
- **13,441 total matches** across all tournaments
- **Per tournament**: ~19 matches average
- **Coverage**: Doubles and singles across all rounds

## 🛠️ Technologies Used

- **Python 3.14+**
- **requests** - HTTP requests with retry logic
- **BeautifulSoup4** - HTML parsing
- **pandas** - Data processing and CSV export
- **selenium** - Browser automation (for social media)
- **webdriver-manager** - ChromeDriver management

## 📝 Scrapers Explained

### Tournament & Match Scraper
**File:** `match-results/scrape_padelfip_calendar_and_results.py`

- Fetches calendar pages by year
- Extracts tournament info (dates, locations, status)
- Discovers tournament day links
- Parses match scores from results widget
- Handles errors and retries gracefully
- Respects rate limits (0.4s delay between requests)

**Features:**
- ✓ Multi-year support (2023-2026)
- ✓ Retry logic with exponential backoff
- ✓ Progress tracking
- ✓ CSV export with structured data

### Venue Scraper
**File:** `courts-and-venues/scrape_venues_and_courts.py`

- Visits each tournament page
- Extracts venue name from structured data
- Parses venue address
- Identifies court count (practice courts)
- Captures indoor/outdoor indicators

**Coverage:** 185 venues with names, 144 with addresses

### Time Dimension Enrichment
**File:** `bi-analytics/add_time_dimensions.py`

Adds temporal context for BI analysis:
- Year, Month, Quarter, Week
- Season (Winter/Spring/Summer/Autumn)
- Pre/Post season indicators
- Days since start (trend baseline)

**Purpose:** Enables forecasting, trend analysis, and KPI dashboards

### Social Media Scrapers
**Files:** `social-media/youtube_scraper.py` and `social_media_scraper.py`

- YouTube (official API - free tier available)
- Instagram/Twitter/Facebook (browser automation)
- Templates for manual collection

## 📊 Data Quality

| Dataset | Records | Completeness | Status |
|---------|---------|--------------|--------|
| Tournaments | 692 | ~95% | ✓ Complete |
| Match Results | 13,441 | ~90% | ✓ Complete |
| Venues | 692 | 27% names, 21% addresses | ⚠️ Partial |
| Time Dimensions | 13,441 | 100% | ✓ Complete |

## 🔍 Sample Queries

```python
import pandas as pd

# Load tournament data with time dimensions
df = pd.read_csv('bi-analytics/tournaments_with_time_dimensions.csv')

# Year-over-year growth
df.groupby('Year').size()

# Peak season analysis
df[df['Pre_Post_Season'] == 'Peak Season'].groupby('Month_Name').size()

# Venue distribution
venues = pd.read_csv('courts-and-venues/venues_and_courts.csv')
venues['venue_name'].value_counts()
```

## 💡 Use Cases

### 1. Business Intelligence
- Tournament trend analysis
- Growth forecasting
- Seasonal pattern detection
- Venue performance metrics

### 2. Player Analytics
- Career tournament participation tracking
- Performance by season
- Head-to-head records
- Rankings trends

### 3. Tournament Planning
- Optimal tournament scheduling
- Venue demand forecasting
- Prize money benchmarking
- Player distribution analysis

## ⚙️ Configuration

### Rate Limiting
Default: 0.4 seconds between requests
```python
--delay 0.4  # Adjust in scraper arguments
```

### Debug Mode
```bash
python scraper.py --max-events 10  # Test with 10 events only
```

### Custom Output
```bash
python scraper.py --out-tournaments tournaments.csv --out-results matches.csv
```

## ⚠️ Important Notes

1. **Rate Limiting**: Scrapers include respectful delays to avoid overwhelming servers
2. **Terms of Service**: Always check website ToS before scraping
3. **Updates**: Re-run scrapers periodically to capture new data
4. **API Keys**: YouTube scraper can use free API tier (10K quota/day)

## 🚀 Next Steps

1. **Set up BI Dashboard** - Power BI, Tableau, or Metabase
2. **Historical Analysis** - Include 2023-2024 data for longer trends
3. **Player Tracking** - Link match results to player profiles
4. **Forecasting** - Build growth prediction models
5. **Social Integration** - Automate social media metrics collection

## 📞 Support

Issues or improvements? Check:
- `Data_to_extract.pdf` - Original requirements
- Individual README files in each folder
- Script help: `python scraper.py --help`

## 📄 License

This project is for personal/research use. Respect padelfip.com and premierpadel.com terms of service.

---

**Last Updated:** February 5, 2026  
**Status:** ✓ Production Ready  
**Data Coverage:** 2025-2026 (692 tournaments, 13,441 matches)
