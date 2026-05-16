from __future__ import annotations

import logging

from iall_teams import IAll_Teams
from ifile_handler import IFile_Handler
from utils import Utils


class All_Teams(IAll_Teams):

    def __init__(self, ifile_handler: IFile_Handler):
        self.all_teams = None
        self.teams_for_year = {}
        self.ifile_handler = ifile_handler


    def get_all_teams(self):
        if self.all_teams is None:
            self.all_teams = self.ifile_handler.get_all_teams()
            if self.all_teams is None:
                logging.error("Failed to load teams data.")
                return {}
        return self.all_teams


    def get_all_teams_for_year(self, year: str) -> dict:
        if year not in self.teams_for_year:
            if self.all_teams is None:
                self.get_all_teams()
            self.teams_for_year[year] = self.__filter_for_year(self.all_teams, int(year))
        return self.teams_for_year[year]


    def year_is_valid_for_team(self, team_data: dict, year: int) -> bool:
        if year == 2020:
            logging.info("Ignoring year 2020 due to Covid")
            return False
        if "years" not in team_data:
            return True
        years_data = team_data["years"]
        if ("missing" in years_data and year in years_data["missing"]) or \
            ("last" in years_data and year > years_data["last"]) or \
            ("first" in years_data and year < years_data["first"]):
            return False
        return True


    def __filter_for_year(self, dict, year: int):
        filtered_teams = {}
        for team_name in self.all_teams:
            team_data = self.all_teams[team_name]
            if self.year_is_valid_for_team(team_data, year):
                filtered_teams[team_name] = team_data
        return filtered_teams


