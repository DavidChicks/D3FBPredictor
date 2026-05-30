class ITeams():
        
    def get_team_games_from_web(self, team: str, year: int) -> list[dict]:
        pass

    def get_game_stats(self, game_url: str) -> dict:
        pass

    def get_and_save_game_stats(self, game_url: str, year: str) -> bool:
        pass