"""Fetch https://www.d3football.com/teams/index and prepare it for parsing.

Folder structure:
data/
  games/
    [year]/
      {games.json}    e.g., 09_11_katn.json:  {teams; scores; stats}
  teams/
    all_teams.json                              {team: team_url_part}
    {team_name.json}    e.g., linfield.json:    {name team_name, link: team_url_part, games: {year: [games]}
  averages/
    [year]/
      {team_name.json}    e.g., linfield.json:    {name team_name, link: team_url_part, avearge stats}
      
"""
from __future__ import annotations

import json
import logging
import os
from ifile_handler import IFile_Handler
from utils import Utils

DATA_ROOT = "data"
TEAMS_FOLDER = "teams"
GAMES_FOLDER = "games"
AVERAGE_FOLDER = "averages"
ALL_TEAMS_FILE_NAME = "__all_teams"
NORMALIZATION_FILE_NAME = "__normalization.json"


class File_Handler(IFile_Handler):
    def get_teams_root(self):
        return os.path.join(DATA_ROOT, TEAMS_FOLDER, "")


    def __get_team_file_path_name(self, team_name: str):
        file_name = Utils.normalize_name(team_name) + ".json"
        file_path_name = os.path.join(self.get_teams_root(), file_name)
        return file_path_name


    def load_game_file(self, year: str, game_file_name: str) -> dict:
        file_path = os.path.join(DATA_ROOT, GAMES_FOLDER, year, game_file_name)
        return self.__load_file(file_path, False)


    def load_team_file(self, team_name: str, none_if_missing):
        team_file = self.__get_team_file_path_name(team_name)
        file_contents = self.__load_file(team_file, True)
        if file_contents is not None:
            return file_contents
        return None if none_if_missing else {} # {"name": team_name, "games": {}}


    def load_averages_file(self, year: str, file_name: str) -> dict:
        team_file = os.path.join(DATA_ROOT, AVERAGE_FOLDER, year, file_name)
        file_contents = self.__load_file(team_file, True)
        if file_contents is not None:
            return file_contents
        return None


    def __load_file(self, file_path_name: str, create_if_missing: bool = False):
        if not os.path.isfile(file_path_name):
            if create_if_missing:
                logging.info(f"File, {file_path_name}, not found; creating new file.")
            return None
        try:
            with open(file_path_name, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Failed to load data for file, {file_path_name}: {e}")
            return None


    def save_all_teams(self, teams: dict) -> None:
        try:
            
            self.__ensure_all_dirs()
            out_path = self.__get_team_file_path_name(ALL_TEAMS_FILE_NAME)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(teams, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Failed to save all teams to {out_path}: {e}")


    def save_ai_normalization_file(self, year: str, normalization_data: dict) -> None:
        try:
            self.__ensure_averages_year_dir(year)
            normalization_file_path = os.path.join(DATA_ROOT, AVERAGE_FOLDER, year, NORMALIZATION_FILE_NAME)
            with open(normalization_file_path, "w", encoding="utf-8") as f:
                json.dump(normalization_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Failed to save AI normalization file for year {year}: {e}")


    def __ensure_all_dirs(self):
        data_dir = os.path.join(".", DATA_ROOT)
        os.makedirs(os.path.dirname(data_dir), exist_ok=True)
        teams_folder = os.path.join(data_dir, TEAMS_FOLDER)
        os.makedirs(os.path.dirname(teams_folder), exist_ok=True)
        games_dir = os.path.join(data_dir, GAMES_FOLDER)
        os.makedirs(os.path.dirname(games_dir), exist_ok=True)
        averages_dir = os.path.join(data_dir, AVERAGE_FOLDER)
        os.makedirs(os.path.dirname(averages_dir), exist_ok=True)
        #for year in range(1999, 2026):
        #    game_year_dir = os.path.join(games_dir, str(year))
        #    os.makedirs(os.path.dirname(game_year_dir), exist_ok=True)


    def __ensure_game_year_dir(self, year: str):
        self.__ensure_all_dirs()
        games_year_dir = os.path.join(DATA_ROOT, GAMES_FOLDER, year)
        os.makedirs(games_year_dir, exist_ok=True)


    def __ensure_averages_year_dir(self, year: str):
        self.__ensure_all_dirs()
        averages_dir = os.path.join(DATA_ROOT, AVERAGE_FOLDER)
        year_dir = os.path.join(averages_dir, year)
        os.makedirs(averages_dir, exist_ok=True)
        os.makedirs(year_dir, exist_ok=True)


    def get_all_teams(self):
        all_teams_path = self.__get_team_file_path_name(ALL_TEAMS_FILE_NAME)
        if not os.path.exists(all_teams_path):
            logging.info(f"All teams file not found at {all_teams_path}")
            return None
        try:
            with open(all_teams_path, "r", encoding="utf-8") as f:
                teams = json.load(f)
            logging.info(f"Loaded all teams from {all_teams_path} (count={len(teams)})")
            return teams
        except Exception as e:
            logging.error(f"Failed to load all teams from {all_teams_path}: {e}")
            return None


    def get_all_game_file_names(self, year: str) -> list:
        game_files = []
        games_year_dir = os.path.join(DATA_ROOT, GAMES_FOLDER, year)

        # Only list files in the given directory
        with os.scandir(games_year_dir) as entries:
            for entry in entries:
                if entry.is_file():
                    game_files.append(entry.name)
        return game_files


    def get_all_averages_files(self, year: str) -> list:
        average_files = []
        averages_year_dir = os.path.join(DATA_ROOT, AVERAGE_FOLDER, year)
        # Only list files in the given directory
        with os.scandir(averages_year_dir) as entries:
            for entry in entries:
                if entry.is_file():
                    if entry.name.endswith(".json") and entry.name != NORMALIZATION_FILE_NAME:  # Only Json files, but exclude the normalization file
                        average_files.append(entry.name)
        return average_files


    def load_ai_normalization_file(self, year: str) -> dict:
        normalization_file_path = os.path.join(DATA_ROOT, AVERAGE_FOLDER, year, NORMALIZATION_FILE_NAME)
        if not os.path.exists(normalization_file_path):
            logging.info(f"Normalization file not found at {normalization_file_path}")
            return None
        try:
            with open(normalization_file_path, "r", encoding="utf-8") as f:
                normalization_data = json.load(f)
            print(f"Loaded normalization data from {normalization_file_path}")
            return normalization_data
        except Exception as e:
            logging.error(f"Failed to load normalization data from {normalization_file_path}: {e}")
            return None


    def update_team_file(self, team_name: str, year: str, year_games: dict):
        team_data = self.load_team_file(team_name, False)
        team_data[year] = year_games
        team_file_name = self.__get_team_file_path_name(team_name)
        try:
            with open(team_file_name, "w", encoding="utf-8") as f:
                json.dump(team_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Failed to update team file for {team_name} at {team_file_name}: {e}")


    def save_game_file(self, game_url: str, stats: dict, year: str):
        game_file_name = game_url.split("/")[-1].split(".")[0] + ".json"
        year = year if year is not None else game_file_name[:4]
        self.__ensure_game_year_dir(year)
        games_year_dir = os.path.join(DATA_ROOT, GAMES_FOLDER, year)
        os.makedirs(games_year_dir, exist_ok=True)
        file_path = os.path.join(games_year_dir, game_file_name)

        try:
            os.makedirs(games_year_dir, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            logging.debug(f"Saved game stats to {file_path}")
        except Exception as e:
            logging.error(f"Failed to save stats to {file_path}: {e}")

       
    def save_statisical_file(self, team_name: str, year: str, stats: dict):
        team_file_name = Utils.normalize_name(team_name) + ".json"
        self.__ensure_averages_year_dir(year)
        averages_year_dir = os.path.join(DATA_ROOT, AVERAGE_FOLDER, year)
        os.makedirs(averages_year_dir, exist_ok=True)
        file_path = os.path.join(averages_year_dir, team_file_name)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Failed to save stats to {file_path}: {e}")


    def team_file_exists(self, team: str) -> bool:
        file_path = self.__get_team_file_path_name(team)
        return os.path.exists(file_path) and os.path.isfile(file_path)


    def game_file_exists(self, year: str, game_file_name: str) -> bool:
        games_year_dir = os.path.join(DATA_ROOT, GAMES_FOLDER, year)
        # os.makedirs(os.path.dirname(games_year_dir), exist_ok=True)
        file_path = os.path.join(games_year_dir, game_file_name)
        return os.path.exists(file_path) and os.path.isfile(file_path)

