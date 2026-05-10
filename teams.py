"""Fetch https://www.d3football.com/teams/index and prepare it for parsing.
Usage:
  python get_teams.py --force # re-fetch and overwrite
"""
from __future__ import annotations
import re
from typing import Optional
import file_handler
from all_teams import All_Teams
from url_utils import Url_Utils
from file_handler import File_Handler
from parse_game_data_file import Parse_Game_Data_File
from utils import Utils
import time

class Teams:

    def __init__(self, file_handler: File_Handler):
        self.file_handler = file_handler

    def __get_team_url_part(self, team: str) -> str:
        all_teams = All_Teams.get_all_teams(self.file_handler)
        url_part = all_teams.get(team)["link"] if team in all_teams else None
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


    def get_team_games_from_web(self, team: str, year: int) -> list[dict]:
        team_url_part = self.__get_team_url_part(team)
        retries = 3
        try:
            page = Url_Utils.get_team_page(team_url_part, year, 3)
        except Exception as e:
            print(f"Error fetching team page for {team} in year {year}: {e}")
            return None
        if page is None:
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
                # print(f" @@ row_text: {row_text}")
                tds = row.find_all("td")
                if len(tds) < 4:
                    if not "Overall record:" in row_text and not "Conference:" in row_text:
                        print(f"Cannot find expected table data cells with {row_text}")
                    continue

                location = tds[1].get_text().strip()[:2]
                is_home = location == "vs"
                #if not (is_home or location == "at"):
                    #print(f"  Location not found: {location}; assuming away")


                # TODO look for anchors in specific table data cells
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
                    "is_home": is_home
                }
                d3games.append(new_game)
        return d3games


    def get_game_stats(self, game_url: str) -> Optional[dict]:
        try:
            game_page = Url_Utils.get_game_page(game_url, 3)
            if game_page is None:
                print("Failed to get game page.")
                return None
        except Exception as e:
            print(f"Error fetching game page for {game_url}: {e}")
            return None
        parser = Parse_Game_Data_File()
        stats = parser.get_game_stats(game_page)
        score = parser.get_game_score(game_page)
        if score:
            stats.update(score)
        return stats


    def get_and_save_game_stats(self, game_url: str, year: str) -> bool:
        stats = self.get_game_stats(game_url)
        if stats is None:
            return False
        self.file_handler.save_game_file(game_url, stats, year)
        return True

    def get_and_save_all_teams(self):
        all_teams = self.get_all_teams_page()
        self.file_handler.save_all_teams(all_teams)
        return all_teams
