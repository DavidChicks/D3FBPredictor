

from ifile_handler import IFile_Handler
from utils import Utils


class All_Teams:
    teams = None

    @staticmethod
    def get_all_teams(ifile_handler: IFile_Handler):
        if All_Teams.teams is None:
            All_Teams.teams = ifile_handler.get_all_teams()
            if All_Teams.teams is None:
                print("Failed to load teams data.")
                return []
        return All_Teams.teams



