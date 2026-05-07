"""Fetch https://www.d3football.com/teams/index and prepare it for parsing.

Usage:
  python get_teams.py         # fetch and save to data/teams_index.html (uses cache)
  python get_teams.py --force # re-fetch and overwrite
"""
from __future__ import annotations

import argparse
import json
from re import A
#import logging
import requests
from typing import Optional

from averaging import Averaging
from file_handler import File_Handler
from teams import Teams
from year_games import Year_Games


def main() -> None:

    parser = argparse.ArgumentParser()
    # parser.add_argument("--force", "-f", action="store_true", help="re-fetch even if cached")
    # parser.add_argument("--out", "-o", default=DEFAULT_SAVE_PATH, help="output file path")
    parser.add_argument("--year", "-y", help="year (2 or 4 digit) to fetch games for (a/all for all)")
    parser.add_argument("--team", "-t", default="a/all", help="team name to fetch games for (a/all for all)")
    parser.add_argument("--allteam", "-at", action="store_true", help="fetch all teams data (no game data)")
    parser.add_argument("--stats", "-s", action="store_true", help="calculate stats for team / year")
    parser.add_argument("--force", "-f", action="store_true", help="re-fetch even if cached")
    args = parser.parse_args()
    print(f"args: {args})")
    print(f"args[year]: {args.year}")
    print(f"args[allteam]: {args.allteam}")
    print(f"args[team]: {args.team}")
    print(f"args[force]: {args.force}")

    # logging.basicConfig(level=logging.INFO, "https://www.d3football.com/teams/index", force=args.force)
    if args.allteam:
        teams = Teams()
        print("Fetching all teams...")
        all_teams = teams.get_and_save_all_teams()
        return

    # TODO verify arguments are valid (e.g. year is 2 or 4 digits or "a/all", team is in all_teams or "a/all")

    year = args.year
    if year is None:
        print("Must speicficy a year (-year / -y)")
        return
    else:
        print(f"Year argument provided: {args.year}")
    team = args.team
    force = args.force
    # TODO: verify that year and team are valid (e.g. year is 4 digits, team is in all_teams)
    
    if args.stats:
        print(f"Calculating stats for team {team} in year {year}...")
        averaging = Averaging(team=team, year=year)
        games = averaging.get_team_year_files()
        return



    year_games = Year_Games()
    if team in ("a", "all"):
        games = year_games.get_all_games_for_all_team_in_year(year, force)
    else:
        games = year_games.get_all_game_for_team_in_year(team, year, force)


if __name__ == "__main__":
    main()
