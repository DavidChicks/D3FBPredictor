from __future__ import annotations

import logging

from iall_teams import IAll_Teams
from ifile_handler import IFile_Handler
from utils import Utils


class All_Teams(IAll_Teams):

    def __init__(self, ifile_handler: IFile_Handler):
        self.all_teams = None
        self.renamed = {}
        self.teams_for_year = {}
        self.ifile_handler = ifile_handler


    def get_all_teams(self):
        if self.all_teams is None:
            all_teams = self.ifile_handler.get_all_teams()
            self.__separate_primaries_and_renames(all_teams)
            if self.all_teams is None:
                logging.error("Failed to load teams data.")
                return {}
        return self.all_teams


    def get_all_teams_for_year(self, year: str) -> dict:
        if year not in self.teams_for_year:
            if self.all_teams is None:
                self.get_all_teams()
            all_teams = self.all_teams
            all_teams = self.__filter_for_year(all_teams, int(year))
            self.teams_for_year[year] = all_teams
        return self.teams_for_year[year]


    def year_is_valid_for_team(self, team_data: dict, year: int) -> bool:
        if year == 2020:
            logging.info("Ignoring year 2020 due to Covid")
            return False
        years_data = team_data.get("years", None)
        if years_data is None:
            return True
        if ("missing" in years_data and year in years_data["missing"]) or \
            ("last" in years_data and year > years_data["last"]) or \
            ("first" in years_data and year < years_data["first"]):
            return False
        return True


    def get_primary_team_name(self, team_name: str) -> str:
        if self.all_teams is None or len(self.all_teams) == 0:
            self.get_all_teams()
        normalized_name = Utils.normalize_name(team_name)
        if normalized_name in self.renamed:
            team_data = self.renamed.get(normalized_name, None)
            if team_data is not None and team_data.get("primary_name", None) is not None:
                return team_data["primary_name"]
        return normalized_name


    def __filter_for_year(self, teams: dict, year: int):
        filtered_teams = {}
        for team_name in teams:
            team_data = self.all_teams.get(team_name)
            if self.year_is_valid_for_team(team_data, year):
                filtered_teams[team_name] = team_data
        return filtered_teams


    def __separate_primaries_and_renames(self, all_teams: dict):
        self.all_teams = {k: v for k, v in all_teams.items() if self.__is_primary_team(v, k)}
        self.renamed = {k: v for k, v in all_teams.items() if not self.__is_primary_team(v, k)}


    def __is_primary_team(self, team_data: dict, team_name: str) -> bool:
        return "primary_name" not in team_data or team_data["primary_name"] == team_name
