"""Fetch https://www.d3football.com/teams/index and prepare it for parsing.

Usage:
  python get_teams.py         # fetch and save to data/teams_index.html (uses cache)
  python get_teams.py --force # re-fetch and overwrite
"""
from __future__ import annotations

import argparse
import json
#import logging
import requests
from typing import Optional

from file_handler import File_Handler
from teams import Teams #, get_team_page, get_team_games
from year_games import Year_Games



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

if __name__ == "__main__":
    main()
