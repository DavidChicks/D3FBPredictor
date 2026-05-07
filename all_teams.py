

from file_handler import File_Handler
from utils import Utils


class All_Teams:
    _instance = None
    teams = None
    file_handler = File_Handler()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(All_Teams, cls).__new__(cls)
        return cls._instance


    @staticmethod
    def get_all_teams():
        all_teams = All_Teams()
        if all_teams.teams is None:
            all_teams.teams = all_teams.file_handler.get_all_teams()
            if all_teams.teams is None:
                print("Failed to load teams data.")
                return []
        return all_teams.teams



