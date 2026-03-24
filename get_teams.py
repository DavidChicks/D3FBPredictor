"""Fetch https://www.d3football.com/teams/index and prepare it for parsing.

Usage:
  python get_teams.py         # fetch and save to data/teams_index.html (uses cache)
  python get_teams.py --force # re-fetch and overwrite
"""
from __future__ import annotations

import argparse
import os
import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup
import json

URL_ROOT = "https://www.d3football.com"
URL = "https://www.d3football.com/teams/index"
DEFAULT_SAVE_PATH = os.path.join("data", "teams_index.html")


def fetch_url(url: str, timeout: int = 15) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; d3-teams-scraper/1.0)"
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def save_html(html: str, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def load_html(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def get_page(save_path: str = DEFAULT_SAVE_PATH, force: bool = False) -> BeautifulSoup:
    """Return a BeautifulSoup for the teams index page.

    If a saved copy exists and force is False, the saved copy will be used.
    Otherwise the page is fetched and saved to `save_path`.
    """
    if not force and os.path.exists(save_path):
        logging.info("Loading cached page from %s", save_path)
        html = load_html(save_path)
    else:
        logging.info("Fetching %s", URL)
        html = fetch_url(URL)
        save_html(html, save_path)
        logging.info("Saved page to %s", save_path)

    # Create parsing-ready BeautifulSoup object
    soup = BeautifulSoup(html, "html.parser")
    return soup


def get_teams_page(save_path: str = DEFAULT_SAVE_PATH, force: bool = False) -> BeautifulSoup:
    soup = get_page(save_path, force=force)
    teams_info = soup.find_all("div", class_="teaminfo")  # sanity check for expected content
    print(f"Found {len(teams_info)} teaminfo divs in the page.")
    teams_table = teams_info[0]
    teams = {}

    rows = teams_table.find_all("tr")
    for row in rows:
        # get the first anchor in the row
        anchor = row.find("a")
        if not anchor:
            continue
        link = anchor.get("href", "").strip()
        text = anchor.get_text(strip=True)
        # teams.append({"text": text, "link": link})
        teams[text] = link
        print(f"Found anchor: text={text!r}, link={link!r}")

    # save teams dict to a JSON file next to the saved HTML
    teams_out_dir = os.path.dirname(save_path) or "data"
    teams_out_path = os.path.join(teams_out_dir, "teams.json")
    try:
        os.makedirs(os.path.dirname(teams_out_path), exist_ok=True)
        with open(teams_out_path, "w", encoding="utf-8") as f:
            json.dump(teams, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(teams)} teams to {teams_out_path}")
    except Exception as e:
        print(f"Failed to save teams to {teams_out_path}: {e}")

    return teams


def get_team_page(team_url: str, year: int = None) -> Optional[BeautifulSoup]:
    url = URL_ROOT + team_url
    if (year is not None):
        url.replace("..", year)
    print("looking for team page at {url}")
    return get_page(url)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", "-f", action="store_true", help="re-fetch even if cached")
    parser.add_argument("--out", "-o", default=DEFAULT_SAVE_PATH, help="output file path")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    teams = get_teams_page(save_path=args.out, force=args.force)

    linfield = get_team_page("linfield", None)
    print(f"Linfield team page: {linfield if linfield else 'Not found'}")
    # minimal confirmation output
    # print(f"Prepared BeautifulSoup; title=\"{soup.title.string if soup.title else 'N/A'}\"")


if __name__ == "__main__":
    main()
