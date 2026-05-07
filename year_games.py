import time

from ast import Dict
from calendar import Day

from all_teams import All_Teams
from file_handler import File_Handler
from teams import Teams
from utils import Utils
from url_utils import Url_Utils

class Year_Games():
    year = None 
    file_handler = File_Handler()
    teams = Teams()


    def get_all_game_for_team_in_year(self, team_raw: str, year: str, force) -> bool:
        at_least_one_file_updated = False
        all_teams = All_Teams.get_all_teams()
        team_name = Utils.normalize_name(team_raw)
        if team_name not in all_teams:
            print(f"Unknown team, {team_raw} ({team_name})")
            return []

        games = self.teams.get_team_games(team_name, year, force)
        print(f"Found {len(games)}; games: {games}")
        if games is None:
            print(f"Failed to find games, skipping year, {year} for team, {team_name}")
            return
        all_games_data = []
        for game in games:
            if game is None or "game_link" not in game or "opponent_name" not in game or game["game_link"] is None or game["opponent_name"] is None:
                print(f"Skipping game with missing data: {game}")
                continue
            game_data = {}
            game_file_name = game["game_link"].split("/")[-1].replace(".xml", ".json")
            game_data["game_file"] = game_file_name
            opponent_normalized = Utils.normalize_name(game["opponent_name"])
            game_data["opponent"] = opponent_normalized
            game_data["is_home"] = game["is_home"]
            week = self.__get_week_from_file_name(game_file_name)
            if week is None:
                print(f"Failed to extract week from game file name: {game_file_name}")
                continue
            # add this game's data to the list for that week
            Utils.add_element_to_list_at_index(all_games_data, week, game_data)

            file_already_exists = self.file_handler.game_file_exists(year, game_file_name)
            if file_already_exists and not force:
                print(f"Game file already exists for {game['game_link']}, skipping fetch.")
                continue

            self.teams.get_and_save_game_stats(game["game_link"])
            at_least_one_file_updated = True
            time.sleep(3)

        # TODO: keep existing data if the file already exists, and only add new games to it (don't overwrite existing data)
        self.file_handler.update_team_file(team_name, year, all_games_data)
        return at_least_one_file_updated


    def get_all_games_for_all_team_in_year(self, year: str, force=False):
        all_teams = All_Teams.get_all_teams()
        for team_name in all_teams:
            updateMade = self.get_all_game_for_team_in_year(team_name, year, force)
            if updateMade:
                print("     Sleeping for 30 seconds to avoid overwhelming the server...")
                time.sleep(30)
                print("     Done sleeping, continuing to next team.")


    def __get_week_from_file_name(self, file_name: str) -> int:
        # extract the week from a file name like "20240907_linfield_wooster.json"
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
        
        total_days = (month - 9) * 30 + day
        if month > 10: # October has 31 days, so we need to account for that
            total_days += 1

        if year and year > 1999:
            extra_days = (year - 1999)
            # If leap year, increase by 2
            leap_days = int((year - 1996) / 4) # - (year_int - 2000) // 100 + (year_int - 2000) // 400
            extra_days += leap_days
            if extra_days >= 7:
                extra_days = extra_days % 7
            total_days += extra_days

        return (int(total_days / 7) - 1)

