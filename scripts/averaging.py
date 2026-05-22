"""
Average stats for a given year team
Mean (average), Median, and Standard Deviation for each stat over the games of the year
Create a dictionary conveying all the averages
    team_all_stats
    opponent_all_stats
    TBD team_home_stats
    TBD team_away_stats
    TBD opponent_home_stats
    TBD opponent_away_stats
"""
from __future__ import annotations

import json
import logging
import re
import statistics
from iall_teams import IAll_Teams
from ifile_handler import IFile_Handler
from parse_game_data_file import Parse_Game_Data_File

class Averaging:
    MINIMUM_GAMES = 3
    team = None
    year = None
    team_all_stats = {}
    opp_all_stats = {}
    away_count = 0
    home_count = 0
    too_few_games = []
    errors = []

    def __init__(self, ifile_handler: IFile_Handler, iall_teams: IAll_Teams, team: str, year: str):
        """Create an Averaging instance that may operate on a given file.

        Args:
            filename: path to a file to be associated with this Averaging instance.
        """
        self.team = iall_teams.get_primary_team_name(team)
        self.year = year
        self.ifile_handler = ifile_handler  

    @staticmethod
    def calculate_and_save_stats_for_all_teams(iall_teams: IAll_Teams, ifile_handler: IFile_Handler, year: str): # , week: int = 11):
        all_teams = iall_teams.get_all_teams_for_year(year)
        Averaging.too_few_games = []
        Averaging.errors = []
        for team_name in all_teams:
            averaging = Averaging(ifile_handler=ifile_handler, iall_teams=iall_teams, team=team_name, year=year)
            games = averaging.calculate_and_save_stats()
        if len(Averaging.too_few_games) > 0:
            logging.info(f"Teams with too few games to calculate stats for year {year}:")
            for team in Averaging.too_few_games:
                logging.info(f"  {team}")
        if len(Averaging.errors) > 0:
            logging.error(f"Errors encountered during stats calculation for year {year}:")
            for error in Averaging.errors:
                logging.error(f"  {error}")


    def calculate_and_save_stats(self): # , week: int = 11):
        logging.info(f"Calculating stats for {self.team} - {self.year}")
        stats_for_year = self.__get_team_year_files()
        if len(stats_for_year) == 0:
            return
        self.ifile_handler.save_statisical_file(self.team, self.year, stats_for_year)


    @staticmethod
    def __parse_numeric(v) -> float:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v).strip()
        if s == "":
            return None
        # handle fractional forms like '3/5'
        if "/" in s:
            parts = s.split("/")
            try:
                nums = [float(p) for p in parts if re.search(r"\d", p)]
                if len(nums) >= 2:
                    return nums[0] / nums[1] if nums[1] != 0 else None
                if len(nums) == 1:
                    return nums[0]
            except Exception:
                pass
        # find first numeric token (handles percentages, simple numbers)
        m = re.search(r"-?\d+(?:\.\d+)?", s)
        if m:
            try:
                return float(m.group())
            except Exception:
                return None
        return None


    def __load_team_year_file(self):
        team_data = self.ifile_handler.load_team_file(self.team, False)
        if (team_data is None) or (self.year not in team_data):
            return None
        return team_data[self.year]


    def __get_team_year_files(self) -> dict:
        logging.info(f"Calculating stats for team {self.team} in year {self.year}...")
        team_year_data = self.__load_team_year_file()
        if team_year_data is None or not isinstance(team_year_data, list):
            return []
        if len(team_year_data) < Averaging.MINIMUM_GAMES or \
            len(list(filter(lambda x: x is not None, team_year_data))) < Averaging.MINIMUM_GAMES:
            logging.info(f"  Too few games, {len(team_year_data)}, skipping")
            Averaging.too_few_games.append(self.team)
            return []
        game_lists = {
            "away": [],
            "home": [],
           }
        self.__create_stat_arrays()
        week = 0
        for weekly_game in team_year_data:
            if not weekly_game == None and isinstance(weekly_game, dict):
                game_file =  weekly_game["game_file"]
                is_home = weekly_game["is_home"]
                if isinstance(game_file, str) and game_file.strip() != "" and isinstance(is_home, bool):
                    if is_home:
                        game_lists["home"].append(game_file)
                    else:
                        game_lists["away"].append(game_file)
            week += 1
        logging.info(f"    home: {game_lists['home']}")
        logging.info(f"    away: {game_lists['away']}")

        for game_file in game_lists["home"]:
            self.__load_game_file(game_file, True)
        for game_file in game_lists["away"]:
            self.__load_game_file(game_file, False)

        result = {}
        result["team_stats"] = self.__calcuatate_mean_median_stddev_for_all_stats(self.team_all_stats)
        result["opp_stats"] = self.__calcuatate_mean_median_stddev_for_all_stats(self.opp_all_stats)
        return result


    def __create_stat_arrays(self):
        stat_names = Parse_Game_Data_File().get_stat_names()
        for stat in stat_names:
            self.team_all_stats[stat] = []
            self.opp_all_stats[stat] = []
        self.team_all_stats["score"] = []
        self.opp_all_stats["score"] = []


    def __load_game_file(self, game_file: str, is_home: bool):
        game_data = self.ifile_handler.load_game_file(year=self.year, game_file_name=game_file)
        if (game_data is None) or (not isinstance(game_data, dict)):
            error_message = f"Failed to load game file {game_file} for year {self.year}"
            logging.error(error_message)
            Averaging.errors.append(error_message)
            return

        team_stats = game_data["home_stats"] if is_home else game_data["away_stats"]
        opp_stats = game_data["away_stats"] if is_home else game_data["home_stats"]
        team_score = 0
        opp_score = 0

        stat_names = Parse_Game_Data_File().get_stat_names()

        for stat in stat_names:
            if stat in team_stats and isinstance(team_stats.get(stat, 0.0), (int, float)):
                self.team_all_stats[stat].append(team_stats.get(stat, 0.0))
            if stat in opp_stats and isinstance(team_stats.get(stat, 0.0), (int, float)):
                self.opp_all_stats[stat].append(opp_stats.get(stat, 0.0))
        self.team_all_stats["score"].append(game_data["home_score"] if is_home else game_data["away_score"])
        self.opp_all_stats["score"].append(game_data["away_score"] if is_home else game_data["home_score"])


    def __calcuatate_mean_median_stddev_for_all_stats(self, all_stats: dict) -> dict:
        stat_names = all_stats.keys()
        result = {}
        for stat in stat_names:
            values = all_stats.get(stat, [])
            nums = [self.__parse_numeric(v) for v in values if self.__parse_numeric(v) is not None]
            count = len(nums)
            if count == 0:
                result[stat] = {"mean": None, "median": None, "stddev": None, "count": 0}
                continue
            mean = statistics.mean(nums)
            median = statistics.median(nums)
            stddev = statistics.pstdev(nums)
            # result[stat] = {"mean": mean, "median": median, "stddev": stddev, "count": count}
            result[stat + "_mean"] = mean
            result[stat + "_median"] = median
            result[stat + "_stddev"] = stddev
            # result[stat + "_count"] = count
        return result


    def __calcuatate_mean_median_stddev(self, stat_for_all_games: dict) -> dict:
        """Calculate mean, median, and standard deviation for each stat in
        `self.team_all_stats`. Assumes each value is a list (possibly containing
        non-numeric items) and filters/parsess numeric values before
        computing statistics.
        Returns a mapping stat -> { mean, median, stddev, count }.
        """
        result = {}
        for stat, values in stat_for_all_games.items():
            # Assume `values` is a list of numeric values
            nums = list(values)
            count = len(nums)
            if count == 0:
                result[stat] = {"mean": None, "median": None, "stddev": None, "count": 0}
                continue

            mean = statistics.mean(nums)
            median = statistics.median(nums)
            # population std dev; returns 0.0 for a single value
            stddev = statistics.pstdev(nums)

            # result[stat] = {"mean": mean, "median": median, "stddev": stddev, "count": count}
            result[stat + "_mean"] = mean
            result[stat + "_median"] = median
            result[stat + "_stddev"] = stddev

            if stat.endswith("_efficiency") or stat.endswith("_per_play"):
                efficiency = True if stat.endswith("_efficiency") else False
                base = stat.rsplit("_efficency", 1)[0] if efficiency else stat.rsplit("_yards_per_play", 1)[0]
                conv_key = f"{base}_conversions" if efficiency else f"{base}_yards"
                count_key = f"{base}_count" if efficiency else f"{base}_plays"
                total_counts = sum(self.team_all_stats[count_key])
                if total_counts > 0:
                    total_conversions = sum(self.team_all_stats[conv_key])
                    conv_rate = total_conversions / total_counts
                    result[stat + "_overall"] = conv_rate

        return result
