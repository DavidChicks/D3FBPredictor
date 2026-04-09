"""Fetch https://www.d3football.com/teams/index and prepare it for parsing.

Usage:
  python get_teams.py         # fetch and save to data/teams_index.html (uses cache)
  python get_teams.py --force # re-fetch and overwrite
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import pprint
import re
import requests
from typing import Optional
from bs4 import BeautifulSoup

from parse_game_data_file import Parse_Game_Data_File
from url_utils import Url_Utils

URL_ROOT = "https://www.d3football.com/"
URL = "https://www.d3football.com/teams/index"
DEFAULT_SAVE_PATH = os.path.join("data", "teams_index.html")


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
    return Url_Utils.get_page(url)


def get_team_games(team_url: str, year: int) -> list[dict]:
    print(f"Getting games for team {team_url} in year {year}")
    soup = get_team_page(team_url, year)
    if (soup is None):
        print("  Failed to get team page.")
        return None
    print("getting schedule table")
    teams_schedule = soup.find_all("table", class_="schedule") 
    if (teams_schedule is None or teams_schedule[0] is None):
        print("  Failed to find schedule table on team page.")
        return None
    print(f"  teams_schedule: teams_schedule")
    rows = teams_schedule[0].find_all("tr")
    print(f"  Processing rows: {str(len(rows))}")
    d3games = []
    for row in rows:
        opponent_link = None
        game_link = None
        opponent_name = None
        opponent_link = None
        print(f"  Processing row")
        row_text = row.get_text()
        
        if "•" in row_text:
            print(f"    Found marker '•' in row text")
            anchors = row.find_all("a")
            for a in anchors:
                if a.get_text(strip=True) == "BX":
                    game_link=a.get("href", "").strip()
                else:
                    if opponent_link is None:
                        opponent_link = a.get("href", "").strip()
                    if opponent_name is None:
                        opponent_name = a.get_text(strip=True)
            new_game = {
                "game_link": game_link,
                "opponent_link": opponent_link,
                "opponent_name": opponent_name,
            }
            d3games.append(new_game)
            print(f"    Found {len(anchors)} anchors in row: {[a.get_text(strip=True) for a in anchors]}")
        else:
            print(f"    No marker '•' found in row text ({row.get_text(strip=True)})-- not a D3 opponent")
    return d3games


def get_game_page(game_url: str) -> Optional[BeautifulSoup]:
    print(f"Getting game page for {game_url}")
    url = URL_ROOT + game_url
    print(f"  looking for game page at {url}")
    return Url_Utils.get_page(url)


def get_game_stats(game_url: str) -> Optional[dict]:
    game_page = get_game_page(game_url)
    if game_page is None:
        print("  Failed to get game page.")
        return None
    parser = Parse_Game_Data_File()
    stats = parser.get_game_stats(game_page)
    score = parser.get_game_score(game_page)
    if score:
        stats.update(score)
    return stats


def get_and_save_game_stats(game_url: str, out_path: str) -> None:
    stats = get_game_stats(game_url)
    end = game_url.split("/")[-1]
    parts = end.split(".")[0].split("_")
    # ensure parts[0] is 8 characters long and all digits (YYYYMMDD)
    if not parts:
        print(f"Unexpected file name format; no parts found in '{without_extension}'")
        return stats

    if not (len(parts[0]) == 8 and parts[0].isdigit()):
        print(f"Unexpected file name format; expected parts[0] to be 8 digits but got: {parts[0]!r}")

    year_prefix = parts[0][:4]
    date = parts[0][4:]
    
    file_path = os.path.join(out_path, f"{year_prefix}", f"{year_prefix}_{date}_{parts[1]}.json")

    # save the stats object as JSON to file_path
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        print(f"Saved stats to {file_path}")
    except Exception as e:
        print(f"Failed to save stats to {file_path}: {e}")

    return stats


def main() -> None:

    parser = argparse.ArgumentParser()
    parser.add_argument("--force", "-f", action="store_true", help="re-fetch even if cached")
    parser.add_argument("--out", "-o", default=DEFAULT_SAVE_PATH, help="output file path")
    args = parser.parse_args()

    # logging.basicConfig(level=logging.INFO, "https://www.d3football.com/teams/index", force=args.force)
    # get_all_teams_page("https://www.d3football.com/teams/index")

    # games = get_team_games("linfield", 2021)
    # print(f"Found games for Linfield in 2021")
    # pprint.pp(games)
    game_stats = get_and_save_game_stats("/seasons/2014/boxscores/20141213_katn.xml", os.path.join("data", "games"))
    pprint.pp(game_stats)


if __name__ == "__main__":
    main()
