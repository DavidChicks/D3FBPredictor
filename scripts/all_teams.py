

from iall_teams import IAll_Teams
from ifile_handler import IFile_Handler
from utils import Utils


class All_Teams(IAll_Teams):

    def __init__(self, ifile_handler: IFile_Handler, team: str = "", year: str=""):
        """Create an Averaging instance that may operate on a given file.

        Args:
            filename: path to a file to be associated with this Averaging instance.
        """
        self.all_teams = None
        self.teams_for_year = {}
        self.ifile_handler = ifile_handler


    def get_all_teams(self):
        if self.all_teams is None:
            self.all_teams = self.ifile_handler.get_all_teams()
            if self.all_teams is None:
                print("Failed to load teams data.")
                return {}
        return self.all_teams


    def get_all_teams_for_year(self, year: str) -> dict:
        if year not in self.teams_for_year:
            if self.all_teams is None:
                self.get_all_teams()
            self.teams_for_year[year] = self.__filter_for_year(self.all_teams, int(year))
        return self.teams_for_year[year]


    def __filter_for_year(self, dict, year: int):
        filtered_teams = {}
        for team_name in self.all_teams:
            team_data = self.all_teams[team_name]
            if "years" in team_data:
                year_data = team_data["years"]
                if ("missing" not in year_data or year not in year_data["missing"]) or \
                    ("first" not in year_data or year >= year_data["first"]) or \
                    ("last" not in year_data or year <= year_data["last"]):
                    filtered_teams[team_name] = team_data
            else:
                filtered_teams[team_name] = team_data
        return filtered_teams


