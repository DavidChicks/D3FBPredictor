"""Fetch https://www.d3football.com/teams/index and prepare it for parsing.
Usage:
  python get_teams.py --force # re-fetch and overwrite
"""
from __future__ import annotations
import re
from typing import Optional
import file_handler
from url_utils import Url_Utils
from file_handler import File_Handler
from parse_game_data_file import Parse_Game_Data_File
from utils import Utils

class Teams:
    file_handler = File_Handler()
    all_teams = None

    def __get_team_url_part(self, team: str) -> str:
        if (self.all_teams is None):
            self.all_teams = self.file_handler.get_all_teams()
            if (self.all_teams is None):
                print("Failed to load teams data.")
                return []
        url_part = self.all_teams.get(team)["link"] if team in self.all_teams else None
        return url_part if url_part is not None else team


    def get_all_teams_page(self, force: bool = False) -> dict:
        all_teams_page = "https://www.d3football.com/teams/index"
        page = Url_Utils.get_page(all_teams_page, force=force)
        teams_info = page.find_all("div", class_="teaminfo")  # sanity check for expected content
        teams_table = teams_info[0]
        teams = {}

        rows = teams_table.find_all("tr")
        for row in rows:
            anchor = row.find("a")
            if not anchor:
                continue
            link = anchor.get("href", "").strip()
            parts = link.split("/")
            name = anchor.get_text(strip=True)
            key = Utils.normalize_name(name)

            # find the segment after 'teams/' and before the next '/'
            m = re.search(r"teams/([^/]+)", link)
            if m and len(m.groups()) > 0:
                link_key = m.group(1)
                teams[key] = {"name": name, "link": link_key }
            else:
                print(f"Unexpected link format for team '{name}': {link}")

        return teams


    def get_team_games(self, team: str, year: int) -> list[dict]:
        team_url_part = self.__get_team_url_part(team)
        page = Url_Utils.get_team_page(team_url_part, year)
        if (page is None):
            print("  Failed to get team page.")
            return None
        teams_schedule = page.find_all("table", class_="schedule") 
        if (teams_schedule is None or len(teams_schedule) == 0 or teams_schedule[0] is None):
            print("  Failed to find schedule table on team page.")
            return None
        rows = teams_schedule[0].find_all("tr")
        d3games = []
        for row in rows:
            opponent_link = None
            game_link = None
            opponent_name = None
            opponent_link = None
            row_text = row.get_text()
        
            if "•" in row_text:
                anchors = row.find_all("a")
                for a in anchors:
                    if a.get_text(strip=True) == "BX":
                        game_link=a.get("href", "").strip()
                    else:
                        if opponent_link is None:
                            opponent_link = a.get("href", "").strip()
                        if opponent_name is None:
                            opponent_name = a.get_text(strip=True)
                new_game = {
                    "game_link": game_link,
                    "opponent_link": opponent_link,
                    "opponent_name": opponent_name,
                }
                d3games.append(new_game)
        return d3games


    def get_game_stats(self, game_url: str) -> Optional[dict]:
        game_page = Url_Utils.get_game_page(game_url)
        if game_page is None:
            print("  Failed to get game page.")
            return None
        parser = Parse_Game_Data_File()
        stats = parser.get_game_stats(game_page)
        score = parser.get_game_score(game_page)
        if score:
            stats.update(score)
        return stats


    def get_and_save_game_stats(self, game_url: str) -> None:
        stats = self.get_game_stats(game_url)
        file_handler = File_Handler()
        file_handler.save_game_file(game_url, stats)


