"""Fetch https://www.d3football.com/teams/index and prepare it for parsing.

Usage:
  python get_teams.py         # fetch and save to data/teams_index.html (uses cache)
  python get_teams.py --force # re-fetch and overwrite
"""
from __future__ import annotations

import argparse
import logging
import sys


sys.path.insert(1, './scripts')

from all_teams import All_Teams
from averaging import Averaging
from build_ai_data import Build_AI_Data
from file_handler import File_Handler
from url_handler import Url_Handler
from all_teams import All_Teams
from teams import Teams
from year_games import Year_Games


def main() -> None:
    fmt = '%(message)s'
    logging.basicConfig(level=logging.INFO, format=fmt)

    parser = argparse.ArgumentParser()
    # parser.add_argument("--force", "-f", action="store_true", help="re-fetch even if cached")
    # parser.add_argument("--out", "-o", default=DEFAULT_SAVE_PATH, help="output file path")
    parser.add_argument("--year", "-y", help="year (2 or 4 digit)")
    parser.add_argument("--team", "-t", default="a/all", help="team name to fetch games for (a/all for all)")
    parser.add_argument("--allteam", "-at", action="store_true", help="fetch all teams data (no game data) - no year/team used")
    parser.add_argument("--ai_generator", "-ai", action="store_true", help="build the ai input data files for the specified year")
    parser.add_argument("--games", "-g", action="store_true", help="get the games for team / year")
    parser.add_argument("--stats", "-s", action="store_true", help="calculate stats for team / year")
    parser.add_argument("--force", "-f", action="store_true", help="re-fetch even if cached")
    args = parser.parse_args()

    file_handler = File_Handler()
    url_handler = Url_Handler()
    all_teams = All_Teams(file_handler)
    teams = Teams(ifile_handler=file_handler, iurl_handler=url_handler, iall_teams=all_teams)

    # logging.basicConfig(level=logging.INFO, "https://www.d3football.com/teams/index", force=args.force)
    if args.allteam:
        logging.info("Fetching all teams...")
        all_teams = teams.get_and_save_all_teams()
        return

    # TODO verify arguments are valid (e.g. year is 2 or 4 digits or "a/all", team is in all_teams or "a/all")

    year = args.year
    if year is None:
        logging.error("Must speicficy a year (-year / -y)")
        return
    team = args.team
    force = args.force
    # TODO: verify that year and team are valid (e.g. year is 4 digits, team is in all_teams)
    
    if args.games:
        logging.info(f"Fetching games for team {team} in year {year}...")
        year_games = Year_Games(ifile_handler=file_handler, iall_teams=all_teams, teams=teams)
        if team in ("a", "all"):
            games = year_games.get_all_games_for_all_team_in_year(year, force)
        else:
            games = year_games.get_all_game_for_team_in_year(team, year, force)

    if args.stats:
        if team in ("a", "all"):
            Averaging.calculate_and_save_stats_for_all_teams(iall_teams=all_teams, ifile_handler=file_handler, year=year)
        else:
            averaging = Averaging(ifile_handler=file_handler, team=team, year=year)
            averaging.calculate_and_save_stats()

    if (args.ai_generator):
        logging.info(f"Building AI data for year {year}...")
        ai_data_builder = Build_AI_Data(ifile_handler=file_handler, year=year)
        ai_data_builder.build_ai_data()


if __name__ == "__main__":
    main()
