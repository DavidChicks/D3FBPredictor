"""
Average stats for a given year team

Create a dictionary conveying all the averages
    team_all_stats
    opponent_all_stats
    team_home_stats
    team_away_stats
    oppoenent_home_stats
    oppoenent_away_stats
"""


import json
import statistics
from iall_teams import IAll_Teams
from ifile_handler import IFile_Handler

class Averaging:
    team = None
    year = None
    team_all_stats = {}
    opp_all_stats = {}
    away_count = 0
    home_count = 0

    def __init__(self, ifile_handler: IFile_Handler, iall_teams: IAll_Teams, team: str = "", year: str=""):
        """Create an Averaging instance that may operate on a given file.

        Args:
            filename: path to a file to be associated with this Averaging instance.
        """
        self.team = team
        self.year = year
        self.ifile_handler = ifile_handler
        self.iall_teams = iall_teams


    def calculate_stats(self): # , week: int = 11):
        games = self.get_team_year_files()


    def average_away_stats_from_files(self, file_paths: list[str]) -> dict[str, float]:
        # wrapper that reads files then computes averages
        away_list = self.read_away_stats_from_files(file_paths)
        return self.compute_averages_from_away_stats(away_list)


    def read_away_stats_from_files(self, file_paths: list[str]) -> list[dict]:
        """Read JSON files and return a list of `away_stats` dicts found in them."""
        away_list: list[dict] = []
        for path in file_paths:
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
            except Exception as e:
                print(f"Failed to open/parse '{path}': {e}")
                continue

            away = data.get("away_stats") or {}
            if isinstance(away, dict):
                away_list.append(away)
        return away_list


    @staticmethod
    def _parse_numeric(v) -> float:
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


    @staticmethod
    def compute_averages_from_stats(away_stats_list: list[dict]) -> dict[str, float]:
        """Compute averages for each stat key from a list of away_stats dicts."""
        sums: dict[str, float] = {}
        counts: dict[str, int] = {}

        for away in away_stats_list:
            if not isinstance(away, dict):
                continue
            for key, raw_val in away.items():
                val = Averaging._parse_numeric(raw_val)
                if val is None:
                    continue
                sums[key] = sums.get(key, 0.0) + val
                counts[key] = counts.get(key, 0) + 1

        averages: dict[str, float] = {}
        for k, s in sums.items():
            c = counts.get(k, 0)
            if c > 0:
                averages[k] = s / c
        return averages

    
    def __load_team_year_file(self):
        team_data = self.ifile_handler.load_team_file(self.team, False)
        if (team_data is None) or (self.year not in team_data):
            return None
        return team_data[self.year]


    def get_all_teams_for_year_files(self, year: str) -> dict[str, list[str]]:
        all_teams = self.iall_teams.get_all_teams(self.ifile_handler)
        for team_name in all_teams:
            averaging = Averaging(ifile_handler=self.ifile_handler, team=team_name, year=year)
            games = averaging.get_team_year_files()


    def get_team_year_files(self) -> dict:
        print(f"Calculating stats for team {self.team} in year {self.year}...")
        team_year_data = self.__load_team_year_file()
        if team_year_data is None or not isinstance(team_year_data, list):
            return []
        game_lists = {
            "away": [],
            "home": [],
           }
        self.__create_stat_arrays()
        week = 0
        for weekly_game in team_year_data:
            if  not weekly_game == None and isinstance(weekly_game, dict):
                game_file =  weekly_game["game_file"]
                is_home = weekly_game["is_home"]
                if isinstance(game_file, str) and game_file.strip() != "" and isinstance(is_home, bool):
                    if is_home:
                        game_lists["home"].append(game_file)
                    else:
                        game_lists["away"].append(game_file)
            week += 1
        print(f"    home: {game_lists['home']}")
        print(f"    away: {game_lists['away']}")

        for game_file in game_lists["home"]:
            self.__load_game_file(game_file, True)
        for game_file in game_lists["away"]:
            self.__load_game_file(game_file, False)

        result = {}
        result["team_stats"] = self.__calcuatate_mean_median_stddev_for_all_stats(self.team_all_stats)
        result["opp_stats"] = self.__calcuatate_mean_median_stddev_for_all_stats(self.opp_all_stats)
        self.ifile_handler.save_statisical_file(self.team, self.year, result)
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
            print(f"Failed to load game file {game_file} for year {self.year}")
            return

        team_stats = game_data["home_stats"] if is_home else game_data["away_stats"]
        opp_stats = game_data["away_stats"] if is_home else game_data["home_stats"]
        team_score = 0
        opp_score = 0

        stat_names = Parse_Game_Data_File().get_stat_names()
        for stat in stat_names:
            if stat in team_stats:
                self.team_all_stats[stat].append(team_stats.get(stat, 0.0))
            if stat in opp_stats:
                self.opp_all_stats[stat].append(opp_stats.get(stat, 0.0))
        self.team_all_stats["score"].append(game_data["home_score"] if is_home else game_data["away_score"])
        self.opp_all_stats["score"].append(game_data["away_score"] if is_home else game_data["home_score"])


    def __calcuatate_mean_median_stddev_for_all_stats(self, all_stats: dict) -> dict:
        stat_names = all_stats.keys()
        result = {}
        for stat in stat_names:
            values = all_stats.get(stat, [])
            nums = [self._parse_numeric(v) for v in values if self._parse_numeric(v) is not None]
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
