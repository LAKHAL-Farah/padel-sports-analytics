import argparse
import re
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

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
    date_start: Optional[str]
    date_end: Optional[str]
    location: Optional[str]
    status: Optional[str]


@dataclass
class EventResultsKey:
    event_year: int
    event_id: str


def fetch_html(session: requests.Session, url: str, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            resp = session.get(url, timeout=60)
            resp.raise_for_status()
            return resp.text
        except (requests.RequestException, TimeoutError) as e:
            if attempt < retries - 1:
                print(f"  Retry {attempt + 1}/{retries - 1} after error: {e}")
                time.sleep(2 ** (attempt + 1))  # exponential backoff
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


def extract_event_info_from_container(container: BeautifulSoup, year: int) -> Optional[EventInfo]:
    link = container.find("a", href=EVENT_URL_PATTERN)
    if not link:
        return None
    url = link.get("href")
    if not url:
        return None

    name = normalize_space(link.get_text(" ", strip=True))
    text = normalize_space(" ".join(container.stripped_strings))

    date_match = re.search(
        r"From\s+(\d{2}/\d{2}/\d{4})\s+to\s+(\d{2}/\d{2}/\d{4})", text
    )
    date_start = date_end = None
    location = None
    status = None
    if date_match:
        date_start, date_end = date_match.group(1), date_match.group(2)
        after = text[date_match.end() :].strip()
        status = extract_status(after)
        if status:
            location = after.split(status, 1)[0].strip(" -|")
        else:
            location = after.strip(" -|") if after else None
        location = location if location else None
    else:
        status = extract_status(text)

    return EventInfo(
        year=year,
        name=name,
        url=url,
        date_start=date_start,
        date_end=date_end,
        location=location,
        status=status,
    )


def parse_calendar_year(session: requests.Session, year: int) -> List[EventInfo]:
    html = fetch_html(session, BASE_CALENDAR_URL.format(year=year))
    soup = BeautifulSoup(html, "html.parser")

    events: Dict[str, EventInfo] = {}

    containers = soup.find_all(
        lambda tag: tag.name in {"div", "article", "li", "section"}
        and tag.find("a", href=EVENT_URL_PATTERN)
        and "From" in tag.get_text()
    )

    for container in containers:
        info = extract_event_info_from_container(container, year)
        if not info:
            continue
        if info.url not in events:
            events[info.url] = info

    if not events:
        # fallback: scan all links and create minimal entries
        for link in soup.find_all("a", href=EVENT_URL_PATTERN):
            url = link.get("href")
            if url and url not in events:
                name = normalize_space(link.get_text(" ", strip=True))
                events[url] = EventInfo(
                    year=year,
                    name=name,
                    url=url,
                    date_start=None,
                    date_end=None,
                    location=None,
                    status=None,
                )

    return list(events.values())


def extract_event_results_key(html: str, fallback_year: int, event_url: str) -> Optional[EventResultsKey]:
    year_match = re.search(r"eventYear2\s*=\s*\"(\d{4})\"", html)
    id_match = re.search(r"eventID2\s*=\s*\"(\d+)\"", html)

    if not id_match:
        id_match = re.search(r"idEvent_(\d+)", html)

    event_id = id_match.group(1) if id_match else None

    event_year = None
    if year_match:
        event_year = int(year_match.group(1))
    else:
        url_year_match = re.search(r"-(\d{4})/?$", event_url)
        if url_year_match:
            event_year = int(url_year_match.group(1))
        else:
            event_year = fallback_year

    if not event_id:
        return None

    return EventResultsKey(event_year=event_year, event_id=event_id)


def get_day_links(session: requests.Session, event_code: str) -> Dict[int, str]:
    html = fetch_html(session, f"https://widget.matchscorerlive.com/screen/resultsbyday/{event_code}/1?t=tol")
    soup = BeautifulSoup(html, "html.parser")

    day_labels: Dict[int, str] = {}
    for a in soup.find_all("a", href=re.compile(r"/screen/resultsbyday/")):
        href = a.get("href", "")
        label = normalize_space(a.get_text(" ", strip=True))
        day_num_match = re.search(r"/resultsbyday/[^/]+/(\d+)", href)
        if day_num_match:
            day_num = int(day_num_match.group(1))
            if label:
                day_labels[day_num] = label

    # try to capture current day label (non-link)
    current = soup.find(
        lambda tag: tag.name in {"span", "div", "li"}
        and tag.get("class")
        and any(cls in {"active", "current"} for cls in tag.get("class"))
    )
    if current:
        label = normalize_space(current.get_text(" ", strip=True))
        if label and not any(label == v for v in day_labels.values()):
            # no reliable day number; leave unmapped
            pass

    if not day_labels:
        day_labels[1] = "DAY 1"

    return day_labels


def parse_team_cell(cell_text: str) -> Tuple[str, Optional[str]]:
    status = None
    text = cell_text.strip()
    if text.endswith("RET"):
        status = "RET"
        text = text[:-3].strip()
    return text, status


def extract_scores(cells: List[str]) -> List[str]:
    scores: List[str] = []
    for cell in cells:
        cell = cell.strip()
        if cell == "":
            continue
        if re.fullmatch(r"-", cell):
            scores.append("")
        elif re.search(r"\d", cell):
            scores.append(cell)
    return scores


def parse_results_day(html: str) -> List[dict]:
    soup = BeautifulSoup(html, "html.parser")
    rows_out: List[dict] = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 3:
            continue

        header_cells = [normalize_space(c.get_text(" ", strip=True)) for c in rows[0].find_all(["th", "td"])]
        if len(header_cells) < 2:
            continue

        court = header_cells[0]
        round_name = header_cells[1]

        data_rows: List[List[str]] = []
        for row in rows[1:]:
            cells = [normalize_space(c.get_text(" ", strip=True)) for c in row.find_all(["th", "td"])]
            if not cells:
                continue
            joined = " ".join(cells).upper()
            if "COMPLETED MATCH STATS" in joined:
                continue
            data_rows.append(cells)

        if len(data_rows) < 2:
            continue

        team1_raw = data_rows[0][0]
        team2_raw = data_rows[1][0]
        team1, status1 = parse_team_cell(team1_raw)
        team2, status2 = parse_team_cell(team2_raw)
        status = status1 or status2

        scores1 = extract_scores(data_rows[0][1:])
        scores2 = extract_scores(data_rows[1][1:])

        max_sets = max(len(scores1), len(scores2))
        score_parts = []
        for i in range(max_sets):
            s1 = scores1[i] if i < len(scores1) else ""
            s2 = scores2[i] if i < len(scores2) else ""
            if s1 or s2:
                score_parts.append(f"{s1}-{s2}".strip("-"))
        score = " ".join(score_parts)

        rows_out.append(
            {
                "court": court,
                "round": round_name,
                "team1": team1,
                "team2": team2,
                "score": score,
                "status": status,
            }
        )

    return rows_out


def scrape_match_results_for_event(
    session: requests.Session, event: EventInfo, delay: float = 0.4
) -> List[dict]:
    html = fetch_html(session, event.url)
    results_key = extract_event_results_key(html, event.year, event.url)
    if not results_key:
        return []

    event_code = f"FIP-{results_key.event_year}-{results_key.event_id}"
    day_labels = get_day_links(session, event_code)

    rows: List[dict] = []
    for day_num in sorted(day_labels.keys()):
        day_label = day_labels.get(day_num, f"DAY {day_num}")
        day_url = f"https://widget.matchscorerlive.com/screen/resultsbyday/{event_code}/{day_num}?t=tol"
        day_html = fetch_html(session, day_url)
        match_rows = parse_results_day(day_html)
        for match in match_rows:
            rows.append(
                {
                    "event_name": event.name,
                    "event_url": event.url,
                    "event_year": results_key.event_year,
                    "day_number": day_num,
                    "day_label": day_label,
                    **match,
                }
            )
        time.sleep(delay)

    return rows


def build_dataframes(events: List[EventInfo]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "year": e.year,
                "name": e.name,
                "url": e.url,
                "date_start": e.date_start,
                "date_end": e.date_end,
                "location": e.location,
                "status": e.status,
            }
            for e in events
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape Padelfip calendar and match results.")
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=[2023, 2024, 2025, 2026],
        help="Years to scrape (e.g., --years 2025 2026)",
    )
    parser.add_argument(
        "--out-tournaments",
        default="match-results/padelfip_tournaments.csv",
        help="Output CSV for tournaments",
    )
    parser.add_argument(
        "--out-results",
        default="match-results/match_results.csv",
        help="Output CSV for match results",
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=None,
        help="Limit number of events (debug)",
    )
    parser.add_argument(
        "--skip-results",
        action="store_true",
        help="Only scrape tournaments",
    )
    args = parser.parse_args()

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    all_events: List[EventInfo] = []
    for year in args.years:
        print(f"Fetching tournaments for {year}...", end=" ", flush=True)
        events = parse_calendar_year(session, year)
        all_events.extend(events)
        print(f"✓ ({len(events)} events)")

    if args.max_events:
        all_events = all_events[: args.max_events]
        print(f"Limited to {len(all_events)} events for testing")

    print(f"\nExporting {len(all_events)} tournaments to {args.out_tournaments}...", end=" ", flush=True)
    tournaments_df = build_dataframes(all_events)
    tournaments_df.to_csv(args.out_tournaments, index=False)
    print("✓")

    if args.skip_results:
        return

    all_results: List[dict] = []
    for i, event in enumerate(all_events):
        print(f"[{i+1}/{len(all_events)}] Scraping results for {event.name}...", end=" ", flush=True)
        try:
            matches = scrape_match_results_for_event(session, event)
            all_results.extend(matches)
            print(f"✓ ({len(matches)} matches)")
        except Exception as e:
            print(f"✗ Skipped ({e})")
            continue

    results_df = pd.DataFrame(all_results) if all_results else pd.DataFrame()
    results_df.to_csv(args.out_results, index=False)
    print(f"\nTotal matches extracted: {len(all_results)}")


if __name__ == "__main__":
    main()
