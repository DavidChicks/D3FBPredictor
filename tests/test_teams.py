import sys
import os
# Ensure scripts directory is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../tests')))
from bs4 import BeautifulSoup
import unittest
from unittest.mock import MagicMock

from teams import Teams
from base_mocks import MockIAll_Teams, MockIFile_Handler, MockITeams, MockIUrl_Handler

class MockIUrl_Handler_SimplePage(MockIUrl_Handler):
    def __init__(self, file: str):
        self.file = file

    #def get_team_page(self, game_url: str, max_retries) -> BeautifulSoup:
    #    page = BeautifulSoup("", 'html.parser')
    #    return page

    def get_team_page(self, team: str, year: str, max_retries: int) -> BeautifulSoup:
        file_path = os.path.join(os.path.dirname(__file__), 'web_pages', self.file)
        with open(file_path, mode='r', encoding='utf-8') as file:
            html_string = file.read()
        page = BeautifulSoup(html_string, 'html.parser')
        return page


class TestTeams(unittest.TestCase):
    def setUp(self):
        self.ifile = MockIFile_Handler()
        self.iall = MockIAll_Teams()
        self.iurl = MockIUrl_Handler()
        #self.teams = Teams(self.ifile, self.iurl, self.iall)

    def test_returns_parsed_games(self):
        my_url_mock = MockIUrl_Handler_SimplePage("linfield_2025.html")
        teams = Teams(self.ifile, my_url_mock, self.iall)
        result = teams.get_team_games_from_web("linfield", 2025)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 9)
        opponent_names = ["UW-Oshkosh", "Chapman", "George Fox", "Pacific", "Whitworth", "Pacific Lutheran", "Lewis and Clark", "Puget Sound", "Willamette"]
        opponent_links = ["UW-Oshkosh", "Chapman", "George_Fox", "Pacific", "Whitworth", "Pacific_Lutheran", "Lewis_and_Clark", "Puget_Sound", "Willamette"]
        game_links = [
            "https://www.d3football.com/seasons/2025/boxscores/20250906_41ka.xml",
            "https://www.d3football.com/seasons/2025/boxscores/20250920_6ews.xml",
            "https://www.d3football.com/seasons/2025/boxscores/20251004_iui1.xml",
            "https://www.d3football.com/seasons/2025/boxscores/20251011_e2mj.xml",
            "https://www.d3football.com/seasons/2025/boxscores/20251018_daxb.xml",
            "https://www.d3football.com/seasons/2025/boxscores/20251025_gdc7.xml",
            "https://www.d3football.com/seasons/2025/boxscores/20251101_75we.xml",
            "https://www.d3football.com/seasons/2025/boxscores/20251108_6nz8.xml",
            "https://www.d3football.com/seasons/2025/boxscores/20251115_82vt.xml"
            ]
        is_homes = [True, True, False, True, True,  False, True,False, True]
        for i in range(0, 9):
            self.assertEqual(result[i]['opponent_name'], opponent_names[i])
            self.assertEqual(result[i]['opponent_link'], "https://www.d3football.com/teams/" + opponent_links[i] + "/2025")
            self.assertEqual(result[i]['game_link'], game_links[i])
            self.assertTrue(result[i]['is_home'] == is_homes[i])
        print("  Test finished!")

    #def test_returns_none_on_no_page(self):
    #    # self.iurl.get_team_page.return_value = None
    #    result = self.teams.get_team_games_from_web(self.team, self.year)
    #    self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
