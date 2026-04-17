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
import pprint
import re
import requests
from typing import Optional

DATA_ROOT = "data"
TEAMS_FOLDER = "teams"
GAMES_FOLDER = "games"

class File_Handler:
    def get_teams_root(self):
        return os.path.join(DATA_ROOT, TEAMS_FOLDER, "")

    def get_team_file(self, team_name: str):
        file_name = self.get_teams_root() + team_name + ".json"
        return file_name

    #def get_file_name_root(file_path: str):
    #    filename = os.path.basename(file_path)
    #    without_extension = os.path.splitext(filename)[0]
    #    return without_extension

    def save_all_teams(self, teams: dict[str, str]) -> None:
        print("Saving all teams...")
        try:
            self.__ensure_all_dirs()
            out_path = os.path.join(".", DATA_ROOT, TEAMS_FOLDER, "all_teams.json")
            print(f"Output path for all teams: {out_path}")
            finalize_dict = self.process_all_teams(teams)
            print(f"Finalized teams dict: {finalize_dict}")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(teams, f, indent=2, ensure_ascii=False)
            print(f"Saved all teams to {out_path}")
        except Exception as e:
            print(f"Failed to save all teams to {out_path}: {e}")


    def process_all_teams(self, teams: dict[str, str]):
        print(f"Processing all teams (count={len(teams)})...")
        finalize_dict = {}
        for team_name, team_url in teams.items():
            url_parts = team_url.split("/") if team_url else []

            if len(url_parts) > 2:
                url_part = url_parts[2]
            else:
                url_part = ""
            finalize_dict[team_name] = url_part
        return finalize_dict


    def __ensure_all_dirs(self):
        data_dir = os.path.join(".", DATA_ROOT)
        os.makedirs(os.path.dirname(data_dir), exist_ok=True)
        teams_folder = os.path.join(data_dir, TEAMS_FOLDER)
        os.makedirs(os.path.dirname(teams_folder), exist_ok=True)
        print(f"Ensured teams folder exists at {teams_folder}")
        games_dir = os.path.join(data_dir, GAMES_FOLDER)
        os.makedirs(os.path.dirname(games_dir), exist_ok=True)
        print(f"Ensured games folder exists at {games_dir}")
        #for year in range(1999, 2026):
        #    game_year_dir = os.path.join(games_dir, str(year))
        #    os.makedirs(os.path.dirname(game_year_dir), exist_ok=True)

    def __ensure_game_year_dir(self, year: str):
        self.__ensure_all_dirs()
        games_year_dir = os.path.join(DATA_ROOT, GAMES_FOLDER, year)
        os.makedirs(os.path.dirname(games_year_dir), exist_ok=True)


    def get_all_teams(self):
        all_teams_path = os.path.join(".", DATA_ROOT, TEAMS_FOLDER, "all_teams.json")
        if not os.path.exists(all_teams_path):
            print(f"All teams file not found at {all_teams_path}")
            return None
        try:
            with open(all_teams_path, "r", encoding="utf-8") as f:
                teams = json.load(f)
            print(f"Loaded all teams from {all_teams_path} (count={len(teams)})")
            return teams
        except Exception as e:
            print(f"Failed to load all teams from {all_teams_path}: {e}")
            return None

    def update_team_file(self, team_name: str, year: str, year_games: dict):
        team_file = self.get_team_file(team_name)
        if not os.path.isfile(team_file):
            print(f"Team file not found for {team_name} at {team_file}, creating new file.")
            team_data = {} # {"name": team_name, "games": {}}
        else:
            print(f"Team file found for {team_name}, year: {year}; year_games: {year_games}.")
            try:
                with open(team_file, "r", encoding="utf-8") as f:
                    team_data = json.load(f)
                print(f"Loaded existing team data for {team_name} from {team_file}")
            except Exception as e:
                print(f"Failed to load existing team data for {team_name} from {team_file}: {e}")
                team_data = {} # {"name": team_name, "games": {}}

        team_data[year] = year_games
        #if "games" not in team_data:
        #    team_data["games"] = {}
        #if year not in team_data["games"]:
        #    team_data["games"][year] = []
        #team_data["games"][year].append(game_data)
        try:
            with open(team_file, "w", encoding="utf-8") as f:
                json.dump(team_data, f, indent=2, ensure_ascii=False)
            print(f"Updated team file for {team_name} at {team_file}")
        except Exception as e:
            print(f"Failed to update team file for {team_name} at {team_file}: {e}")

    def save_game_file(self, game_url: str, stats: dict):
        print(f"Saving game stats for {game_url}...")
        game_file_name = game_url.split("/")[-1].split(".")[0] + ".json"
        year = game_file_name[:4]
        print(f"Extracted year '{year}' from game file name '{game_file_name}'")
        # print(f"Ensured teams folder exists at {teams_folder}")
        self.__ensure_game_year_dir(year)
        games_year_dir = os.path.join(DATA_ROOT, GAMES_FOLDER, year)
        os.makedirs(os.path.dirname(games_year_dir), exist_ok=True)
        file_path = os.path.join(games_year_dir, game_file_name)
        print(f"Output path for game stats: {file_path}")

        try:
            os.makedirs(os.path.dirname(games_year_dir), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            print(f"Saved stats to {file_path}")
        except Exception as e:
            print(f"Failed to save stats to {file_path}: {e}")

