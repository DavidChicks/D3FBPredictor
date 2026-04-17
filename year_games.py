from ast import Dict
from calendar import Day

from file_handler import File_Handler
from teams import Teams
from url_utils import Url_Utils

class Year_Games():
    year = None 
    all_teams = None
    file_handler = File_Handler()
    teams = Teams()

    #def __init_(self):
    #    self.year = None
    #    self.all_teams = None
    #    # self.file_handler = File_Handler()


    def get_all_game_for_team_in_year(self, team: str, year: str, force=False):
        if (self.all_teams is None):
            self.all_teams = self.file_handler.get_all_teams()
            if (self.all_teams is None):
                print("Failed to load teams data.")
                return []

        # team_url_part = self.all_teams.get(team)

        games = self.teams.get_team_games(team, year)
        print(f"Games: {games}")
        # Url_Utils.get_team_page(team_url_part, year)
        all_games_data = []
        for game in games:
            # print(f"Processing game: {game}")
            if "game_link" not in game or "opponent_name" not in game or game["game_link"] is None or game["opponent_name"] is None:
                print(f"Skipping game with missing data: {game}")
                continue
            game_data = {}
            game_file_name = game["game_link"].split("/")[-1]
            game_data["game_file"] = game_file_name
            opponent_normalized = self.teams.normalize_name(game["opponent_name"])
            print(f"Normalized opponent name: '{game['opponent_name']}' -> '{opponent_normalized}'")
            game_data["opponent"] = opponent_normalized
            week = self.get_week_from_file_name(game_file_name)
            if week is None:
                print(f"Failed to extract week from game file name: {game_file_name}")
                continue
            # add this game's data to the list for that week
            print("------------------------------")
            print(f"    Adding game data for week {week}: {game_data}")
            self.add_element_to_list_at_index(all_games_data, week, game_data)

            #self.teams.get_game_stats(game["game_link"])
            print(f"    Fetching and saving game stats for game link: {game['game_link']}")
            self.teams.get_and_save_game_stats(game["game_link"])

        # TODO: save game_data to a JSON file named after the team and year, e.g. "data/games/2024/team_name.json"
        # TODO: keep existing data if the file already exists, and only add new games to it (don't overwrite existing data)
        normalized_name = self.teams.normalize_name(team)
        self.file_handler.update_team_file(normalized_name, year, all_games_data)


    def get_week_from_file_name(self, file_name: str) -> int:
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
        
        print(f"Extracted date from file name: year={year}, month={month}, day={day}")
        total_days = (month - 9) * 30 + day
        if month > 10: # October has 31 days, so we need to account for that
            total_days += 1

        print(f"Total days since September 1: {total_days}")
        # Increase by 1 for each year after 1999
        if year and year > 1999:
            extra_days = (year - 1999)

            # If leap year, increase by 2
            leap_days = int((year - 1996) / 4) # - (year_int - 2000) // 100 + (year_int - 2000) // 400
            extra_days += leap_days
            #print(f"    Adding leap days 1: {extra_days}")
            if extra_days >= 7:
                extra_days = extra_days % 7
            #print(f"    Adding leap days 2: {extra_days}")
            total_days += extra_days

        #print(f"Total days since September 1: {total_days}")
        return int(total_days / 7)

    def add_element_to_list_at_index(self, lst: list, index: int, element):
        #print(f"  Adding element at index {index}: {element}")
        while len(lst) <= index:
            lst.append(None)
        lst[index] = element


    def foo():
        for team in teams:
            team_url = teams[team]
            team_page = get_team_page(team_url, year)
            if team_page is None:
                print(f"Failed to get page for team {team} ({team_url})")
                continue
            games = parse_team_games(team_page)
            self.games.extend(games)
