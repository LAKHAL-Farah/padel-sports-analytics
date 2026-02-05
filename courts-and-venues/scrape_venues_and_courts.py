import argparse
import re
import time
from dataclasses import dataclass
from typing import List, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_CALENDAR_URL = "https://www.padelfip.com/calendar/?events-year={year}"
EVENT_URL_PATTERN = re.compile(r"https?://www\.padelfip\.com/events/[^\"'#?\s]+/?")


@dataclass
class EventInfo:
    year: int
    name: str
    url: str
    start_date: str
    end_date: str
    location: str
    status: str


@dataclass
class VenueInfo:
    tournament_name: str
    tournament_url: str
    year: int
    venue_name: Optional[str]
    venue_address: Optional[str]
    venue_city: Optional[str]
    venue_country: Optional[str]
    court_surface: Optional[str]
    num_courts: Optional[int]
    indoor_outdoor: Optional[str]


def fetch_html(session: requests.Session, url: str, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            resp = session.get(url, timeout=60)
            resp.raise_for_status()
            return resp.text
        except (requests.RequestException, TimeoutError) as e:
            if attempt < retries - 1:
                print(f"  Retry {attempt + 1}/{retries - 1} after error: {e}")
                time.sleep(2 ** (attempt + 1))
            else:
                print(f"  Failed after {retries} attempts: {e}")
                raise


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_status(text: str) -> Optional[str]:
    status_match = re.search(
        r"\b(FINISHED|LIVE|REGISTRATION OPEN|REGISTRATION CLOSED)\b", text, re.IGNORECASE
    )
    return status_match.group(1).upper() if status_match else None


def extract_event_info_from_container(container, year: int) -> Optional[EventInfo]:
    link_tag = container.find("a", href=EVENT_URL_PATTERN)
    if not link_tag:
        return None

    url = link_tag["href"]
    name = normalize_space(link_tag.get_text())

    date_div = container.find("div", class_="event-date")
    date_text = normalize_space(date_div.get_text()) if date_div else ""
    
    start_date = ""
    end_date = ""
    if date_text:
        date_match = re.search(r"(\d{1,2}/\d{1,2}/\d{4})\s*-\s*(\d{1,2}/\d{1,2}/\d{4})", date_text)
        if date_match:
            start_date = date_match.group(1)
            end_date = date_match.group(2)

    location_div = container.find("div", class_="event-location")
    location = ""
    if location_div:
        location = normalize_space(location_div.get_text())
        location = location.strip(" -|")

    status_div = container.find("div", class_="event-status")
    status = extract_status(status_div.get_text()) if status_div else ""

    return EventInfo(
        year=year,
        name=name,
        url=url,
        start_date=start_date,
        end_date=end_date,
        location=location,
        status=status or "",
    )


def parse_calendar_year(session: requests.Session, year: int) -> List[EventInfo]:
    url = BASE_CALENDAR_URL.format(year=year)
    html = fetch_html(session, url)
    soup = BeautifulSoup(html, "html.parser")
    
    events_dict = {}
    
    # Find all containers with event links
    containers = soup.find_all(
        lambda tag: tag.name in {"div", "article", "li", "section"}
        and tag.find("a", href=EVENT_URL_PATTERN)
        and "From" in tag.get_text()
    )
    
    for container in containers:
        event = extract_event_info_from_container(container, year)
        if event and event.url not in events_dict:
            events_dict[event.url] = event
    
    # Fallback: scan all links
    if not events_dict:
        for link in soup.find_all("a", href=EVENT_URL_PATTERN):
            url = link.get("href")
            if url and url not in events_dict:
                name = normalize_space(link.get_text())
                events_dict[url] = EventInfo(
                    year=year,
                    name=name,
                    url=url,
                    start_date="",
                    end_date="",
                    location="",
                    status="",
                )
    
    return list(events_dict.values())


def extract_venue_info(session: requests.Session, event: EventInfo) -> VenueInfo:
    """Extract venue and court information from tournament page."""
    try:
        html = fetch_html(session, event.url)
        soup = BeautifulSoup(html, "html.parser")
        
        venue_name = None
        venue_address = None
        venue_city = None
        venue_country = event.location
        court_surface = None
        num_courts = None
        indoor_outdoor = None
        
        text_content = soup.get_text()
        
        # Extract venue name (appears as "VENUE<name>ADDRESS")
        venue_pattern = r"VENUE\s*([^\n]+?)\s*(?:ADDRESS|PRACTICE)"
        venue_match = re.search(venue_pattern, text_content, re.I)
        if venue_match:
            potential_name = normalize_space(venue_match.group(1))
            # Clean up - remove phone numbers, emails, etc
            potential_name = re.sub(r'\d{3,}', '', potential_name)  # Remove long numbers
            potential_name = re.sub(r'phone|email|tel\.?', '', potential_name, flags=re.I)
            potential_name = normalize_space(potential_name)
            if len(potential_name) > 3:
                venue_name = potential_name
        
        # Extract address (appears after "ADDRESS")
        address_pattern = r"ADDRESS\s*([^\n]+?)(?:\s+PRACTICE COURT|\s+TOURNAMENT|\n\s*\n|$)"
        address_match = re.search(address_pattern, text_content, re.I | re.DOTALL)
        if address_match:
            potential_addr = normalize_space(address_match.group(1))
            # Clean up - remove "Order of Play" and other non-address text
            potential_addr = re.sub(r'Order of Play.*', '', potential_addr, flags=re.I)
            potential_addr = re.sub(r'Loading.*', '', potential_addr, flags=re.I)
            potential_addr = re.sub(r'Male.*Female.*', '', potential_addr, flags=re.I)
            potential_addr = normalize_space(potential_addr)
            if len(potential_addr) > 5:
                venue_address = potential_addr
        
        # Extract practice courts count
        practice_match = re.search(r"PRACTICE COURT[S]?\s*(\d+)", text_content, re.I)
        if practice_match:
            num_courts = int(practice_match.group(1))
        
        # Extract court conditions (Indoor/Outdoor)
        court_cond_match = re.search(r"COURT CONDITIONS\s*(Indoor|Outdoor)", text_content, re.I)
        if court_cond_match:
            indoor_outdoor = court_cond_match.group(1).title()
        
        # Method 2: Look for tables with facility information
        tables = soup.find_all("table")
        for table in tables:
            table_text = normalize_space(table.get_text())
            # Skip tables that look like match results or player lists
            if any(x in table_text.lower() for x in ['gender', 'male', 'female', 'pairs', 'match']):
                continue
            
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all(["td", "th"])
                if len(cells) >= 3:
                    cell_texts = [normalize_space(cell.get_text()) for cell in cells]
                    # Check if this looks like a venue row (has name and address-like content)
                    if cell_texts[0] and len(cell_texts[0]) > 3 and not venue_name:
                        # Verify it's not a header or unwanted content
                        if not any(x in cell_texts[0].lower() for x in ['tournament', 'director', 'gender', 'male', 'female']):
                            venue_name = cell_texts[0]
                    
                    # Third or fourth cell might be address (usually longer text with numbers/street info)
                    for i in range(2, len(cell_texts)):
                        if cell_texts[i] and len(cell_texts[i]) > 15 and not venue_address:
                            # Check if it looks like an address (has numbers or street-like content)
                            if re.search(r'\d+|street|avenue|road|calle|rue|via', cell_texts[i], re.I):
                                venue_address = cell_texts[i]
                                break
        
        # Extract city from address if available
        if venue_address:
            # Try to extract city (format: postal_code City_Name (Region))
            city_match = re.search(r"(?:^|\s)(\d{4,5})\s+([A-Z][a-zA-Z\s]+?)(?:\s*\(|\s*,|\s*$)", venue_address)
            if city_match:
                venue_city = city_match.group(2).strip()
        
        return VenueInfo(
            tournament_name=event.name,
            tournament_url=event.url,
            year=event.year,
            venue_name=venue_name,
            venue_address=venue_address,
            venue_city=venue_city or event.location,
            venue_country=venue_country,
            court_surface=court_surface,
            num_courts=num_courts,
            indoor_outdoor=indoor_outdoor,
        )
    
    except Exception as e:
        print(f"✗ ({e})")
        return VenueInfo(
            tournament_name=event.name,
            tournament_url=event.url,
            year=event.year,
            venue_name=None,
            venue_address=None,
            venue_city=event.location,
            venue_country=event.location,
            court_surface=None,
            num_courts=None,
            indoor_outdoor=None,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape Padelfip venue and court data.")
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=[2023, 2024, 2025, 2026],
        help="Years to scrape",
    )
    parser.add_argument(
        "--output",
        default="courts-and-venues/venues_and_courts.csv",
        help="Output CSV file",
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=None,
        help="Limit number of events (debug)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.4,
        help="Delay between requests in seconds",
    )
    args = parser.parse_args()

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    # Collect all events
    all_events: List[EventInfo] = []
    for year in args.years:
        print(f"Fetching tournaments for {year}...", end=" ", flush=True)
        events = parse_calendar_year(session, year)
        all_events.extend(events)
        print(f"✓ ({len(events)} events)")

    if args.max_events:
        all_events = all_events[: args.max_events]
        print(f"Limited to {len(all_events)} events for testing")

    # Extract venue information
    venues: List[VenueInfo] = []
    for i, event in enumerate(all_events):
        print(f"[{i+1}/{len(all_events)}] Extracting venue for {event.name}...", end=" ", flush=True)
        venue = extract_venue_info(session, event)
        venues.append(venue)
        print("✓")
        time.sleep(args.delay)

    # Export to CSV
    print(f"\nExporting {len(venues)} venues to {args.output}...", end=" ", flush=True)
    df = pd.DataFrame([vars(v) for v in venues]) if venues else pd.DataFrame()
    df.to_csv(args.output, index=False)
    print("✓")
    
    if len(venues) > 0:
        print(f"\nSummary:")
        print(f"  Total venues: {len(venues)}")
        print(f"  With venue names: {df['venue_name'].notna().sum()}")
        print(f"  With addresses: {df['venue_address'].notna().sum()}")
        print(f"  With court info: {df['court_surface'].notna().sum()}")


if __name__ == "__main__":
    main()
