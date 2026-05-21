
class IFile_Handler():
    def get_all_teams():
        pass

    def get_all_game_file_names(year: str) -> list:
        pass

    def get_all_game_years() -> list:
        pass

    def get_all_averages_files(year: str) -> list:
        pass

    def game_file_exists(year: str, game_file_name: str) -> bool:
        pass

    def team_file_exists(team_name: str) -> bool:
        pass

    def load_game_file(year: str, game_file_name: str) -> dict:
        pass

    def load_ai_normalization_file(year: str) -> dict:
        pass

    def load_averages_file(year: str, team_name: str) -> list:
        pass

    def load_team_file(team_name: str, none_if_missing: bool = False) -> dict:
        pass

    def save_all_teams(teams: dict) -> None:
        pass

    def save_ai_normalization_file(year: str, normalization_data: dict) -> None:
        pass

    def save_game_file(year: str, game_file_name: str, game_data: dict) -> None:
        pass

    def save_team_file(team_name: str, team_data: dict) -> None:
        pass

    def update_team_file(team_name: str, team_data: dict) -> None:
        pass

