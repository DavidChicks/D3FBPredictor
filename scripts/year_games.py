from __future__ import annotations

from encodings.punycode import T
import logging
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
        self.output = []


    def get_all_game_for_team_in_year(self, team_name_raw: str, year: str, force) -> bool:
        at_least_one_file_updated = False
        all_teams = self.iall_teams.get_all_teams()
        team_name = self.iall_teams.get_primary_team_name(team_name_raw)

        if team_name not in all_teams:
            error_message = f"Unknown team, {team_name_raw} ({team_name})"
            logging.error(error_message)
            self.output.append(error_message)
            return []
        team_data = all_teams[team_name]
        if not self.iall_teams.year_is_valid_for_team(team_data, int(year)):
            logging.info(f"  Skipping year/team (did not play): {year} for {team_name}")
            return []

        games = None
        local_file = False
        (games, local_file) = self.__get_team_file(team_name, year, force)
    
        if games is None:
            error_message = f"Failed to find games, skipping year for team: *** {team_name} - {year}"
            logging.error(error_message)
            self.output.append(error_message)
            return False
        all_games_data = games if local_file else []

        for game in games:
            at_least_one_file_updated = self.__get_game_data(all_games_data, game, year, force) or at_least_one_file_updated

        # TODO: keep existing data if the file already exists, and only add new games to it (don't overwrite existing data)
        if at_least_one_file_updated or not local_file:
            self.ifile_handler.update_team_file(team_name, year, all_games_data, True)
        return at_least_one_file_updated


    def get_all_games_for_all_team_in_year(self, year: str, force=False):
        all_teams = self.iall_teams.get_all_teams()
        for team_name in all_teams:
            updateMade = self.get_all_game_for_team_in_year(team_name, year, force)
            if updateMade:
                logging.info("     Sleeping for 30 seconds to avoid overwhelming the server...")
                time.sleep(30)
                logging.info("     Done sleeping, continuing to next team.")


    def get_output(self) -> list[str]:
        return self.output


    def __get_team_file(self, team_name: str, year: str, force: bool) -> dict:
        if force or not self.ifile_handler.team_file_exists(team_name):
            logging.info(f"Team file does not exist (or --force passed, fetching from web: ***  {team_name} ***.")
            games = self.teams.get_team_games_from_web(team_name, year)
            # local_file = False
            return games, False
        else:
            team_data_all_years = self.ifile_handler.load_team_file(team_name, none_if_missing=True)
            if team_data_all_years is None or str(year) not in team_data_all_years or team_data_all_years[str(year)] is None:
                logging.info(f"Team file does not contain data for year, fetching from web: ***  {team_name} - {year}.")
                games = self.teams.get_team_games_from_web(team_name, year)
                # local_file = False
                return games, False
            else:
                logging.info(f"  Local file found, skipping download: {team_name} - {year}.")
                games = team_data_all_years[str(year)]
                # local_file = True
                return games, True


    def __get_game_data(self, all_games_data: list, game: dict, year: int, force: bool):
        web_game = True if game is not None and "game_link" in game and game["game_link"] is not None and "opponent_name" in game and game["opponent_name"] is not None else False
        local_game = True if game is not None and "game_file" in game and game["game_file"] is not None and "opponent" in game and game["opponent"] is not None else False
        if not web_game and not local_game: # game is None or "game_link" not in game or "opponent_name" not in game or game["game_link"] is None or game["opponent_name"] is None:
            #logging.info(f"      Skipping game with missing data: {game}")
            return False
        game_data = {}
        game_file_name = game["game_file"] if local_game else game["game_link"].split("/")[-1].replace(".xml", ".json")
        game_data["game_file"] = game_file_name
        game_data["opponent"] = game["opponent"] if local_game else self.iall_teams.get_primary_team_name(game["opponent_name"])
        game_data["is_home"] = game["is_home"]
        week = Utils.get_week_from_file_name(game_file_name)
        if week is None:
            error_message = f"Failed to extract week from game file name: {game_file_name}"
            logging.error(error_message)
            self.output.append(error_message)
            return False
        # add this game's data to the list for that week
        Utils.add_element_to_list_at_index(all_games_data, week, game_data)

        file_already_exists = self.ifile_handler.game_file_exists(year, game_file_name)
        if file_already_exists and not force:
            #print(f"      Game file already exists for {game_file_name}, skipping fetch.")
            return False

        year_str = str(year) if local_game else None
        game_link = game["game_link"] if web_game else "/seasons/" + str(year) + "/boxscores/" + game_file_name.replace(".json", ".xml")
        file_saved = self.teams.get_and_save_game_stats(game_link, year_str)
        time.sleep(5)
        if file_saved:
            return True
