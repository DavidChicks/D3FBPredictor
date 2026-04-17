"""Fetch https://www.d3football.com/teams/index and prepare it for parsing.
Usage:
  python get_teams.py --force # re-fetch and overwrite
"""
from __future__ import annotations
from re import I
from typing import Optional
import file_handler
from url_utils import Url_Utils
from file_handler import TEAMS_FOLDER, File_Handler
from parse_game_data_file import Parse_Game_Data_File

class Teams:
    file_handler = File_Handler()
    all_teams = None

    def get_team_url_part(self, team: str) -> str:
        if (self.all_teams is None):
            self.all_teams = self.file_handler.get_all_teams()
            if (self.all_teams is None):
                print("Failed to load teams data.")
                return []
        url_part = self.all_teams.get(team)
        return url_part if url_part is not None else team


    def get_all_teams_page(self, force: bool = False) -> dict:
        #print(f"Getting all teams page (force={force})")
        all_teams_page = "https://www.d3football.com/teams/index"
        page = Url_Utils.get_page(all_teams_page, force=force)
        teams_info = page.find_all("div", class_="teaminfo")  # sanity check for expected content
        #print(f"Found {len(teams_info)} teaminfo divs in the page.")
        teams_table = teams_info[0]
        teams = {}

        rows = teams_table.find_all("tr")
        for row in rows:
            anchor = row.find("a")
            if not anchor:
                continue
            link = anchor.get("href", "").strip()
            text = anchor.get_text(strip=True)
            teams[text] = link

        return teams

    #def save_date_foo():
    #    # save teams dict to a JSON file next to the saved HTML
    #    teams_out_dir = os.path.dirname(save_path) or "data"
    #    teams_out_path = os.path.join(teams_out_dir, "teams.json")
    #    try:
    #        os.makedirs(os.path.dirname(teams_out_path), exist_ok=True)
    #        with open(teams_out_path, "w", encoding="utf-8") as f:
    #            json.dump(teams, f, indent=2, ensure_ascii=False)
    #        print(f"Saved {len(teams)} teams to {teams_out_path}")
    #    except Exception as e:
    #        print(f"Failed to save teams to {teams_out_path}: {e}")
    #    return teams


    #def get_team_page(self, team_url: str, year: int = None) -> Optional[BeautifulSoup]:
    #    print(f"Getting team page for {team_url} (year={year})")
    #    year_str = str(year) + "/" if year is not None else ""
    #    url = URL_ROOT + "teams/"
    #    url += team_url +"/"
    #    url += year_str
    #    print(f"  looking for team page at {url}")
    #    return Url_Utils.get_page(url)


    def get_team_games(self, team: str, year: int) -> list[dict]:
        #print(f"Getting games for team {team} in year {year}")
        team_url_part = self.get_team_url_part(team)
        #print(f"  team_url_part: {team_url_part}")
        page = Url_Utils.get_team_page(team_url_part, year)
        if (page is None):
            print("  Failed to get team page.")
            return None
        #print("getting schedule table")
        teams_schedule = page.find_all("table", class_="schedule") 
        if (teams_schedule is None or len(teams_schedule) == 0 or teams_schedule[0] is None):
            print("  Failed to find schedule table on team page.")
            return None
        #print(f"  teams_schedule: teams_schedule")
        rows = teams_schedule[0].find_all("tr")
        #print(f"  Processing rows: {str(len(rows))}")
        d3games = []
        for row in rows:
            opponent_link = None
            game_link = None
            opponent_name = None
            opponent_link = None
            #print(f"  Processing row")
            row_text = row.get_text()
        
            if "•" in row_text:
                #print(f"    Found marker '•' in row text")
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
                #print(f"    Found {len(anchors)} anchors in row: {[a.get_text(strip=True) for a in anchors]}")
            #else:
                #print(f"    No marker '•' found in row text ({row.get_text(strip=True)})-- not a D3 opponent")
        return d3games


    #def get_game_page(self, game_url: str) -> Optional[BeautifulSoup]:
    #    #print(f"Getting game page for {game_url}")
    #    url = URL_ROOT + game_url
    #    #print(f"  looking for game page at {url}")
    #    return Url_Utils.get_game_page(game_url)
    #    #return get_page(url)


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
        print(f"fetching and saving game stats for {game_url}")
        stats = self.get_game_stats(game_url)
        file_handler = File_Handler()
        file_handler.save_game_file(game_url, stats)


    def foo_get_and_save_game_stats():
        url_file = game_url.split("/")[-1].split(".")[0]
        parts = url_file.split("_")
        # ensure parts[0] is 8 characters long and all digits (YYYYMMDD)
        if not parts:
            print(f"Unexpected file name format; no parts found in '{without_extension}'")
            return stats
        if not (len(parts[0]) == 8 and parts[0].isdigit()):
            print(f"Unexpected file name format; expected parts[0] to be 8 digits but got: {parts[0]!r}")

        year_prefix = parts[0][:4]
        date = parts[0][4:]
    
        # file_path = os.path.join(out_path, f"{year_prefix}", f"{year_prefix}_{date}_{parts[1]}.json")
        file_path = os.path.join(out_path, f"{year_prefix}", f"{url_file}.json")

        # save the stats object as JSON to file_path
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            print(f"Saved stats to {file_path}")
        except Exception as e:
            print(f"Failed to save stats to {file_path}: {e}")

        return stats


    def normalize_name(self, name: str) -> str:
        normalized = name.strip().lower()
        normalized = normalized.replace("&", "and").replace(" ", "_").replace("-", "_").replace(".", "")
        return normalized

