from bs4 import BeautifulSoup
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))
from iall_teams import IAll_Teams
from ifile_handler import IFile_Handler
from iteams import ITeams
from iurl_handler import IUrl_Handler

class MockIAll_Teams(IAll_Teams):
    def get_all_teams(self):
        return {}

    def get_all_teams_for_year(self, year: str) -> dict:
        return {}

    def year_is_valid_for_team(self, team_data: dict, year: int) -> bool:
        return True

    def get_primary_team_name(self, team_name: str) -> str:
        return ""


class MockIFile_Handler(IFile_Handler):
    def get_all_teams(self):
        return {}

    def get_all_game_file_names(self, year: str) -> list:
        return []

    def get_all_game_years(self) -> list:
        return []

    def get_all_averages_files(self, year: str) -> list:
        return []

    def game_file_exists(self, year: str, game_file_name: str) -> bool:
        return True

    def team_file_exists(self, team_name: str) -> bool:
        return True

    def load_game_file(self, year: str, game_file_name: str) -> dict:
        return {}

    def load_ai_normalization_file(self, year: str) -> dict:
        return {}

    def load_averages_file(self, year: str, team_name: str) -> list:
        return []

    def load_team_file(self, team_name: str, none_if_missing: bool = False) -> dict:
        return {}

    def save_all_teams(self, teams: dict) -> None:
        return None

    def save_ai_normalization_file(self, year: str, normalization_data: dict) -> None:
        return None

    def save_game_file(self, year: str, game_file_name: str, game_data: dict) -> None:
        return None

    def save_team_file(self, team_name: str, team_data: dict) -> None:
        return None

    def update_team_file(self, team_name: str, year: str, year_games: list, full_year: bool) -> None:
        return None


class MockITeams(ITeams):
        
    def get_team_games_from_web(self, team: str, year: int) -> list[dict]:
        pass

    def get_game_stats(self, game_url: str) -> dict:
        pass

    def get_and_save_game_stats(self, game_url: str, year: str) -> bool:
        pass


class MockIUrl_Handler(IUrl_Handler):
    def get_team_page(self, team: str, year: str, max_retries: int) -> BeautifulSoup:
        return ""

    def get_game_page(self, game_url: str, max_retries) -> BeautifulSoup:
        return ""
