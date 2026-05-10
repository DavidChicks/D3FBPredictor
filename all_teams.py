

from file_handler import File_Handler
from utils import Utils


class All_Teams:
    teams = None

    @staticmethod
    def get_all_teams(file_handler: File_Handler):
        if All_Teams.teams is None:
            All_Teams.teams = file_handler.get_all_teams()
            if All_Teams.teams is None:
                print("Failed to load teams data.")
                return []
        return All_Teams.teams



