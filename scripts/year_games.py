from __future__ import annotations

from calendar import SEPTEMBER
import time

from ifile_handler import IFile_Handler
from iall_teams import IAll_Teams
from teams import Teams
from utils import Utils

class Year_Games():

    def __init__(self, ifile_handler: IFile_Handler, iall_teams: IAll_Teams, teams: Teams):
        self.ifile_handler = ifile_handler
        self.iall_teams = iall_teams
        self.teams = teams


    def get_all_game_for_team_in_year(self, team_raw: str, year: str, force) -> bool:
        at_least_one_file_updated = False
        all_teams = self.iall_teams.get_all_teams()
        team_name = Utils.normalize_name(team_raw)
        if team_name not in all_teams:
            print(f"Unknown team, {team_raw} ({team_name})")
            return []

        team_data = all_teams[team_name]
        if not self.iall_teams.year_is_valid_for_team(team_data, int(year)):
            print(f"  Skipping year/tema (did not play): {year} for {team_name}")
            return []

        games = None
        local_file = False

        if force or not self.ifile_handler.team_file_exists(team_name):
            print(f"Team file does not exist (or --force passed, fetching from web: ***  {team_name} ***.")
            games = self.teams.get_team_games_from_web(team_name, year)
            local_file = False
        else:
            team_data_all_years = self.ifile_handler.load_team_file(team_name, none_if_missing=True)
            #print(f"Loaded team data for {team_name}: {team_data_all_years}")
            if team_data_all_years is None or str(year) not in team_data_all_years or team_data_all_years[str(year)] is None:
                print(f"Team file does not contain data for year, fetching from web: ***  {team_name} - {year}.")
                games = self.teams.get_team_games_from_web(team_name, year)
                local_file = False
            else:
                print(f"  Local file found, skipping download: {team_name} - {year}.")
                games = team_data_all_years[str(year)]
                local_file = True
    
        if games is None:
            print(f"Failed to find games, skipping year for team: *** {team_name} - {year}")
            return False
        all_games_data = games if local_file else []
        for game in games:
            web_game = True if game is not None and "game_link" in game and game["game_link"] is not None and "opponent_name" in game and game["opponent_name"] is not None else False
            local_game = True if game is not None and "game_file" in game and game["game_file"] is not None and "opponent" in game and game["opponent"] is not None else False
            if not web_game and not local_game: # game is None or "game_link" not in game or "opponent_name" not in game or game["game_link"] is None or game["opponent_name"] is None:
                #print(f"      Skipping game with missing data: {game}")
                continue
            game_data = {}
            game_file_name = game["game_file"] if local_game else game["game_link"].split("/")[-1].replace(".xml", ".json")
            game_data["game_file"] = game_file_name
            game_data["opponent"] = game["opponent"] if local_game else Utils.normalize_name(game["opponent_name"])
            game_data["is_home"] = game["is_home"]
            week = self.__get_week_from_file_name(game_file_name)
            if week is None:
                print(f"Failed to extract week from game file name: {game_file_name}")
                continue
            # add this game's data to the list for that week
            Utils.add_element_to_list_at_index(all_games_data, week, game_data)

            file_already_exists = self.ifile_handler.game_file_exists(year, game_file_name)
            if file_already_exists and not force:
                #print(f"      Game file already exists for {game_file_name}, skipping fetch.")
                continue

            year_str = str(year) if local_game else None
            game_link = game["game_link"] if web_game else "/seasons/" + str(year) + "/boxscores/" + game_file_name.replace(".json", ".xml")
            file_saved = self.teams.get_and_save_game_stats(game_link, year_str)
            if file_saved:
                at_least_one_file_updated = True
            time.sleep(5)

        # TODO: keep existing data if the file already exists, and only add new games to it (don't overwrite existing data)
        if at_least_one_file_updated or not local_file:
            self.ifile_handler.update_team_file(team_name, year, all_games_data)
        return at_least_one_file_updated


    def get_all_games_for_all_team_in_year(self, year: str, force=False):
        all_teams = self.iall_teams.get_all_teams()
        for team_name in all_teams:
            updateMade = self.get_all_game_for_team_in_year(team_name, year, force)
            if updateMade:
                print("     Sleeping for 30 seconds to avoid overwhelming the server...")
                time.sleep(30)
                print("     Done sleeping, continuing to next team.")


    def __get_week_from_file_name(self, file_name: str) -> int:
        # extract the week from a file name like "20240907_linfield_wooster.json"
        # earliest possible game is Sept 1st, so assume the week from 1-7 is first week, etc.
        parts = file_name.split(".")[0].split("_")
        if len(parts) < 2:
            print(f"Unexpected file name format; expected at least 3 parts but got: {parts}")
            return None
        date_part = parts[0]
        if len(date_part) != 8 or not date_part.isdigit():
            print(f"Unexpected date format in file name; expected 8 digits but got: {date_part}")
            return None
        month_day = date_part[4:]
        year = int(date_part[:4])
        month = int(month_day[:2])
        day = int(month_day[2:])
        if (year is None or month is None or day is None):
            print(f"Failed to extract date from file name: {file_name}: year={year}, month={month}, day={day}")
            return None
        
        total_days = (month - 9) * 30 + day - 1 # -1 shift from 1-7 to 0-6
        if month > 10: # October has 31 days, so we need to account for that
            total_days += 1

        return int(total_days / 7)
