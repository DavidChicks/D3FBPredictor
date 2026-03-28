"""Fetch https://www.d3football.com/teams/index and prepare it for parsing.

Usage:
  python get_teams.py         # fetch and save to data/teams_index.html (uses cache)
  python get_teams.py --force # re-fetch and overwrite
"""
from __future__ import annotations

import argparse
import os
import logging
# from re import I
from typing import Optional

import requests
from bs4 import BeautifulSoup
import json

import pprint

URL_ROOT = "https://www.d3football.com/"
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


def get_page(url: str = DEFAULT_SAVE_PATH, force: bool = False) -> BeautifulSoup:
    """Return a BeautifulSoup for the teams index page.

    If a saved copy exists and force is False, the saved copy will be used.
    Otherwise the page is fetched and saved to `save_path`.
    """
    # if not force and os.path.exists(save_path):
    #     logging.info("Loading cached page from %s", save_path)
    #     html = load_html(save_path)
    # else:
    logging.info("Fetching %s", url)
    html = fetch_url(url)
    # save_html(html, save_path)
    # logging.info("Saved page to %s", save_path)

    # Create parsing-ready BeautifulSoup object
    soup = BeautifulSoup(html, "html.parser")
    return soup


def get_all_teams_page(url: str = DEFAULT_SAVE_PATH, force: bool = False) -> BeautifulSoup:
    soup = get_page(url, force=force)
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
    print(f"Getting team page for {team_url} (year={year})")
    year_str = str(year) + "/" if year is not None else ""
    url = URL_ROOT + "teams/"
    url += team_url +"/"
    url += year_str
    print(f"  looking for team page at {url}")
    return get_page(url)


def get_team_games(team_url: str, year: int) -> list[dict]:
    print(f"Getting games for team {team_url} in year {year}")
    soup = get_team_page(team_url, year)
    # print(f"  get_team_page: {soup}")
    if (soup is None):
        print("  Failed to get team page.")
        return None
    # print(f"    Soup: {soup}")
    print("getting schedule table")
    teams_schedule = soup.find_all("table", class_="schedule") 
    if (teams_schedule is None or teams_schedule[0] is None):
        print("  Failed to find schedule table on team page.")
        return None
    print(f"  teams_schedule: teams_schedule")
    rows = teams_schedule[0].find_all("tr")
    print(f"  Processing rows: {str(len(rows))}")
    for row in rows:
        opponent_link = None
        game_link = None
        print(f"  Processing row")
        # search row for the bullet marker "•"
        row_text = row.get_text()
        
        if "•" in row_text:
            print(f"    Found marker '•' in row text")
            anchors = row.find_all("a")
            for a in anchors:
                if a.get_text(strip=True) == "BX":
                    print("    Found game link")
                    game_link=a.get("href", "").strip()
                else:
                    print("    link text: " + a.get_text(strip=True))
            print(f"    Found {len(anchors)} anchors in row: {[a.get_text(strip=True) for a in anchors]}")
        else:
            print(f"    No marker '•' found in row text ({row.get_text(strip=True)})-- not a D3 opponent")


def get_game_page(game_url: str) -> Optional[BeautifulSoup]:
    print(f"Getting game page for {game_url}")
    url = URL_ROOT + game_url
    print(f"  looking for game page at {url}")
    return get_page(url)


def get_game_stats(game_url: str) -> Optional[dict]:
    game_page = get_game_page(game_url)
    if game_page is None:
        print("  Failed to get game page.")
        return None
    teams_table = game_page.find_all("table", class_="all-center")
    if teams_table is None or len(teams_table) == 0:
        print("  Failed to find teams info table on game page.")
        return None
    home_stats = {}
    away_stats = {}
    rows = teams_table[0].find_all("tr")
    stat_splitter_ignore_fields = "stat_splitter_ignore_fields"
    stat_splitter_key_prepend = "prepend"
    stat_splitter = {
        "PassingRushingPenalty": {stat_splitter_ignore_fields: "<br/>", stat_splitter_key_prepend: "First Down by "}
        }
    for row in rows:
        print(f"  Processing row")
        # get the first anchor in the row
        cells = row.find_all("td")
        for cell in cells:
            print(f"    Processing cell: {cell.get_text(strip="True")}")
        if len(cells) != 3:
            print(f"     Incorrect cell count in row ({len(cells)}), skipping")
            continue

        stat = cells[1].get_text(strip=True)
        if stat in stat_splitter:
            stat_spliting = stat_splitter[stat]
            print(f"splitting stat: {stat} into sub stats")
            print(f"     Original cell texts: {row}")
            print(f"     cells[0]: {cells[0]}")
            cell_type = type(cells[0])

            field_names = []
            away_sub_stats = []
            home_sub_stats = []
            for sub_cell in cells[1].children:
                if str(sub_cell) == stat_spliting[stat_splitter_ignore_fields]:
                    print(f"    Ignoring sub-cell: {sub_cell}")
                    continue
                field_names.append(stat_spliting[stat_splitter_key_prepend] + sub_cell.get_text(strip=True))

            for sub_cell in cells[0].children:
                if str(sub_cell) == stat_spliting[stat_splitter_ignore_fields]:
                    print(f"    Ignoring sub-cell: {sub_cell}")
                    continue
                print(f"    Adding away sub stat: {sub_cell.get_text(strip=True)}")
                away_sub_stats.append(sub_cell.get_text(strip=True))

            for sub_cell in cells[2].children:
                if str(sub_cell) == stat_spliting[stat_splitter_ignore_fields]:
                    print(f"    Ignoring sub-cell: {sub_cell}")
                    continue
                print(f"    Adding home sub stat: {sub_cell.get_text(strip=True)}")
                home_sub_stats.append(sub_cell.get_text(strip=True))

            if len(field_names) != len(away_sub_stats) or len(field_names) != len(home_sub_stats):
                print(f"     Incorrect split count in row for stat {stat} (fields={len(field_names)}, away_stats={len(away_stats)}, home_stats={len(home_stats)}), skipping")
                continue

            for i, field_name in enumerate(field_names):
                away_stats[field_name] = away_sub_stats[i]
                home_stats[field_name] = home_sub_stats[i]

        else:
            away_stats[stat] = cells[0].get_text(strip=True)
            home_stats[stat] = cells[2].get_text(strip=True)

    print("========================")
    print("Away stats:")
    pprint.pp(away_stats)
    print("------------------------")
    print("Home stats:")
    pprint.pp(home_stats)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", "-f", action="store_true", help="re-fetch even if cached")
    parser.add_argument("--out", "-o", default=DEFAULT_SAVE_PATH, help="output file path")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # teams = get_all_teams_page(save_path=args.out, force=args.force)

    # linfield = get_team_games("linfield", 2021)
    game_stats = get_game_stats("seasons/2025/boxscores/20251004_xmdh.xml")


if __name__ == "__main__":
    main()
