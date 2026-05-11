
class IFile_Handler():
    def get_all_teams():
        pass

    def game_file_exists(year: str, game_file_name: str) -> bool:
        pass

    def team_file_exists(team_name: str) -> bool:
        pass

    def load_game_file(year: str, game_file_name: str) -> dict:
        pass

    def load_team_file(team_name: str, none_if_missing: bool = False) -> dict:
        pass

    def save_all_teams(teams: dict) -> None:
        pass

    def save_game_file(year: str, game_file_name: str, game_data: dict) -> None:
        pass

    def save_team_file(team_name: str, team_data: dict) -> None:
        pass

    def update_team_file(team_name: str, team_data: dict) -> None:
        pass

