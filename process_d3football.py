"""Fetch https://www.d3football.com/teams/index and prepare it for parsing.

Usage:
  python get_teams.py         # fetch and save to data/teams_index.html (uses cache)
  python get_teams.py --force # re-fetch and overwrite
"""
from __future__ import annotations

import argparse
import logging
from re import A, I
import sys

from scripts import iall_teams


sys.path.insert(1, './scripts')

from all_teams import All_Teams
from averaging import Averaging
from consistency_check import Consistency_Check
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
    parser.add_argument("--consistency", "-c", action="store_true", help="consistency check")
    parser.add_argument("--do_fixes", "-d", action="store_true", help="fix consistency errors (only valid if consistency check also set")
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

    if args.do_fixes and not args.consistency:
        logging.error("The --do_fixes flag is only valid if --consistency is also set")
        return

    year = args.year
    if year is None and (args.games or args.stats):
        logging.error("Must speicficy a year (-year / -y) for games or stats")
        return
    if year is not None and len(year) == 2:
        year = "20" + year
    team = args.team
    force = args.force
    
    output = []
    if args.games:
        message = f"Fetching games for team: {team} in year: {year}..."
        logging.info(message)
        output.append(message)
        year_games = Year_Games(ifile_handler=file_handler, iall_teams=all_teams, teams=teams)
        if team in ("a", "all"):
            games = year_games.get_all_games_for_all_team_in_year(year, force)
        else:
            games = year_games.get_all_game_for_team_in_year(team, year, force)
        output.extend(year_games.get_output())

    consistency_errors = False
    if args.consistency:
        do_fixes = args.do_fixes
        message = f"Checking consistency for year: {year}" + (f" with fixes enabled" if do_fixes else "")
        logging.info(message)
        output.append(message)
        consistency_errors = []
        if year in ("a", "all"):
            consistency_check_success, consistency_errors = Consistency_Check.check_all_years(ifile_handler=file_handler, iall_teams=all_teams, do_fixes=do_fixes)
            output.extend(consistency_errors)
        else:
            consistency_check = Consistency_Check(ifile_handler=file_handler, iall_teams=all_teams, year=year, do_fixes=do_fixes)
            consistency_check.do_consistency_check()
            #consistency_check_success, consistency_errors = consistency_check.do_consistency_check()
            #consistency_errors = consistency_check.get_errors()
            consistency_errors = consistency_check.get_errors()
        result = "Consistency check passed with no errors" if len (consistency_errors) == 0 else "Consistency check found errors"
        output.append(result)
        output.extend(consistency_errors)

    if args.stats:
        message = f"Building stats for team: {team} in year: {year}"
        logging.info(message)
        output.append(message)
        if team in ("a", "all"):
            errors = Averaging.calculate_and_save_stats_for_all_teams(iall_teams=all_teams, ifile_handler=file_handler, year=year)
        else:
            averaging = Averaging(ifile_handler=file_handler, iall_teams=all_teams, team=team, year=year)
            averaging.calculate_and_save_stats()
            errors = averaging.get_errors()
        output.extend(errors)

    if (args.ai_generator):
        logging.info(f"Building AI data")
        from build_ai_data import Build_AI_Data
        ai_data_builder = Build_AI_Data(ifile_handler=file_handler, iall_teams=all_teams)
        ai_data_builder.build_ai_data()

    print("=========== OUTPUT ==========")
    for line in output:
        print(line)

if __name__ == "__main__":
    main()
