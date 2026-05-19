
from bs4 import BeautifulSoup

class IUrl_Handler:

    def get_team_page(team: str, year: str, max_retries: int) -> BeautifulSoup:
        pass

    def get_game_page(game_url: str, max_retries) -> BeautifulSoup:
        pass
