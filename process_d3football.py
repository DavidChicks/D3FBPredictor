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

from file_handler import File_Handler
from teams import Teams #, get_team_page, get_team_games
from parse_game_data_file import Parse_Game_Data_File
from url_utils import Url_Utils
from year_games import Year_Games
import year_games


URL_ROOT = "https://www.d3football.com/"
URL = "https://www.d3football.com/teams/index"
DEFAULT_SAVE_PATH = os.path.join("data", "teams_index.html")


#def get_game_page(game_url: str) -> Optional[BeautifulSoup]:
#    print(f"Getting game page for {game_url}")
#    url = URL_ROOT + game_url
#    print(f"  looking for game page at {url}")
#    return Url_Utils.get_page(url)


#def get_game_stats(game_url: str) -> Optional[dict]:
#    game_page = get_game_page(game_url)
#    if game_page is None:
#        print("  Failed to get game page.")
#        return None
#    parser = Parse_Game_Data_File()
#    stats = parser.get_game_stats(game_page)
#    score = parser.get_game_score(game_page)
#    if score:
#        stats.update(score)
#    return stats


#def get_and_save_game_stats(game_url: str, out_path: str) -> None:
#    stats = get_game_stats(game_url)
#    end = game_url.split("/")[-1]
#    parts = end.split(".")[0].split("_")
#    # ensure parts[0] is 8 characters long and all digits (YYYYMMDD)
#    if not parts:
#        print(f"Unexpected file name format; no parts found in '{without_extension}'")
#        return stats
#
#    if not (len(parts[0]) == 8 and parts[0].isdigit()):
#        print(f"Unexpected file name format; expected parts[0] to be 8 digits but got: {parts[0]!r}")
#
#    year_prefix = parts[0][:4]
#    date = parts[0][4:]
#    
#    file_path = os.path.join(out_path, f"{year_prefix}", f"{year_prefix}_{date}_{parts[1]}.json")
#
#    # save the stats object as JSON to file_path
#    try:
#        os.makedirs(os.path.dirname(file_path), exist_ok=True)
#        with open(file_path, "w", encoding="utf-8") as f:
#            json.dump(stats, f, indent=2, ensure_ascii=False)
#        print(f"Saved stats to {file_path}")
#    except Exception as e:
#        print(f"Failed to save stats to {file_path}: {e}")
#
#    return stats

def get_all_teams() -> dict[str, str]:
    teams = Teams()
    all_teams = teams.get_all_teams_page()
    file_handle = File_Handler()
    file_handle.save_all_teams(all_teams)
    return all_teams


def main() -> None:

    parser = argparse.ArgumentParser()
    # parser.add_argument("--force", "-f", action="store_true", help="re-fetch even if cached")
    # parser.add_argument("--out", "-o", default=DEFAULT_SAVE_PATH, help="output file path")
    parser.add_argument("--year", "-y", default="2025", help="year (2 or 4 digit) to fetch games for (a/all for all)")
    parser.add_argument("--team", "-t", default="a/all", help="team name to fetch games for (a/all for all)")
    parser.add_argument("--allteam", "-at", action="store_true", help="fetch all teams data (no game data)")
    args = parser.parse_args()
    print(f"args: {args})")
    print(f"args[year]: {args.year}")
    print(f"args[allteam]: {args.allteam}")

    # logging.basicConfig(level=logging.INFO, "https://www.d3football.com/teams/index", force=args.force)
    if args.allteam:
        print("Fetching all teams...")
        all_teams = get_all_teams()
        return

    # TODO verify arguments are valid (e.g. year is 2 or 4 digits or "a/all", team is in all_teams or "a/all")

    year = args.year
    if "year" in args and args.year:
        print(f"Year argument provided: {args.year}")
    team = args.team
    # TODO: verify that year and team are valid (e.g. year is 4 digits, team is in all_teams)


    year_games = Year_Games()

    print(f"year_games: {year_games}")
    games = year_games.get_all_game_for_team_in_year("linfield", year)
    # print(f"Found games for Linfield in 2021")
    # print(f"Found {games}")
    # pprint.pp(games)

    # game_stats = teams.get_and_save_game_stats(20141213_katn.xml", os.path.join("data", "games"))
    # pprint.pp(game_stats)


if __name__ == "__main__":
    main()
