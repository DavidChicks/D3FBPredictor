
from dataclasses import field
import logging
from re import S

from iall_teams import IAll_Teams
from ifile_handler import IFile_Handler
from parse_game_data_file import Parse_Game_Data_File
from scripts import ifile_handler
from utils import Utils

class Consistency_Check:
    allowable_nones = {
        "Third_downs_efficiency": "hird_downs_count",
        "Fourth_downs_efficiency": "Fourth_downs_count",
        "Offensive_yards_per_play": "Offensive_plays",
        "Pass_yards_per_play": "Pass_plays",
        "Rush_yards_per_play": "Rush_plays",
        "Punts_yards_average": "Punts_count",
        }

    def __init__(self, ifile_handler: IFile_Handler, iall_teams: IAll_Teams, year: str, do_fixes: bool):
        self.iall_teams = iall_teams
        self.ifile_handler = ifile_handler
        self.year = year
        self.do_fixes = do_fixes
        self.all_teams = iall_teams.get_all_teams_for_year(year)
        self.team_game_data = {}
        self.errors = []
        self.updates = {}
        self.stat_names = Parse_Game_Data_File().get_stat_names()
        self.stat_names.append("score")


    def do_consistency_check(self):
        consistenty = True
        #game_consistency = self.__check_games()
        stats_consistency = self.__check_statistics()


    def get_errors(self) -> list:
        return self.errors


    @staticmethod
    def check_all_years(ifile_handler: IFile_Handler, iall_teams: IAll_Teams, do_fixes: bool) -> bool:
        game_years = ifile_handler.get_all_game_years()
        overall_success = True
        all_errors = []
        for year in game_years:
            consistency_check = Consistency_Check(ifile_handler=ifile_handler, iall_teams=iall_teams, year=year, do_fixes=do_fixes)
            success = consistency_check.do_consistency_check()
            overall_success = overall_success and success
            errors = consistency_check.get_errors()
            all_errors.extend(errors)
        return overall_success, all_errors


    ### GAME CHECKS
    def __check_games(self) -> bool:
        logging.info(f"Performing consistency check of games for year {self.year}...")
        all_games = self.ifile_handler.get_all_game_file_names(self.year)

        for game_file in all_games:
            logging.info(f"Checking game file: {game_file}")
            game_data = self.ifile_handler.load_game_file(self.year, game_file)
            if game_data is None:
                logging.error(f"Failed to load game file: {game_file}")
                continue
            away_team = self.iall_teams.get_primary_team_name(game_data.get("away_team", None))
            if away_team is None:
                logging.error(f"Game file missing away team: {game_file}")
                continue
            home_team = self.iall_teams.get_primary_team_name(game_data.get("home_team", None))
            if home_team is None:
                logging.error(f"Game file missing home team: {game_file}")
                continue
            logging.debug(f"Checking game file: {game_file} - {away_team} @ {home_team}")
            self.__validate_game_team_consistency(game_file, away_team, home_team)

            #self.__team_game_stats_check(game_file, away_team, False)
            #self.__team_game_stats_check(game_file, home_team, True)


        if len(self.errors) > 0:
            for error in self.errors:
                logging.error(f"CONSISTENCY ERROR: {error}")
            if self.do_fixes:
                self.__save_updates()
        else:
            logging.info(f"  Game files are consistent with team data")
        return len(self.errors) == 0, self.errors


    def __validate_game_team_consistency(self, game_name: str, away_team: str, home_team: str) -> dict:
        if away_team not in self.all_teams:
            self.errors.append(f"Team (away), {away_team} not found in all_teams; game: {game_name}")
        if home_team not in self.all_teams: 
            self.errors.append(f"Team (home), {home_team} not found in all_teams; game: {game_name}")

        self.__team_game_consistency_check(game_name, away_team, home_team, False)
        self.__team_game_consistency_check(game_name, home_team, away_team, True)



    def __team_game_consistency_check(self, game_name, team_name, expected_opponent, expected_is_home) -> dict:
        team_game_data = self.__get_team_game_data(team_name, game_name)
        team_game_data_fixed = {}
        if team_game_data is not None:
            update_made = False
            opponent = self.iall_teams.get_primary_team_name(team_game_data.get("opponent", None))
            team_game_name = team_game_data.get("game_file", None)
            team_game_data_fixed = team_game_data.copy() #RDC
            if team_game_data.get("game_file") != game_name:
                self.errors.append(f"Team {team_name} has a game in year {self.year} but file name in team file, {team_game_name}, does not match; game_file: {game_name}")
                team_game_data_fixed["game_file"] = game_name
                update_made = True
            if team_game_data.get("is_home") != expected_is_home:
                self.errors.append(f"Team {team_name} has a game in year {self.year} but is_home does not match expected: {expected_is_home}; game_file: {game_name}")
                team_game_data_fixed["is_home"] = expected_is_home
                update_made = True
            if opponent != expected_opponent:
                self.errors.append(f"Team {team_name} has a game in year {self.year} but opponent, {opponent}, does not match expected: {expected_opponent}; game_file: {game_name}")
                team_game_data_fixed["opponent"] = expected_opponent
                update_made = True
            if update_made:
                #logging.info(f"  Consistency error found for team {team_name} in game {game_name}; updated data: {team_game_data_fixed}")
                self.__add_update(team_name, team_game_data_fixed)
        else:
            team_game_data_fixed = {
                "game_file": game_name,
                "is_home": expected_is_home,
                "opponent": expected_opponent
                }
            self.__add_update(team_name, team_game_data_fixed)


    def __game_file_check(self, game_name: str):
        game_data = self.ifile_handler.load_game_file(self.year, game_name)
        if (game_data is None):
            self.errors.append(f"Failed to load game file: {game_name} for stats check")
            return
        away_team = game_data.get("away_team", None)
        home_team = game_data.get("home_team", None)

        if (away_team is None or home_team is None):
            self.errors.append(f"Game file missing away or home team: {game_name} for stats check")
            return

        away_stats = game_data.get("away_stats", None)
        home_stats = game_data.get("home_stats", None)

        self.__team_game_stats_check(game_name, away_stats, False)
        self.__team_game_stats_check(game_name, home_stats, True)


    def __game_stats_check(self, game_name: str, team_game_data: dict, is_home: bool):
        # tgame_data = self.ifile_handler.load_averages_file(self.year, game_)
        # TODO check stats for game are consistent with home/away and opponent
        for stat_name in self.stat_names:
            stat_value = team_game_data.get(stat_name, None)
            if stat_value not in team_game_data:
                self.errors.append(f"Game {game_name} for team {("home" if is_home else "away")} is missing expected stat: {stat_name}")
                continue
            if stat_value is None:
                if stat_name in allowable_nones and team_game_data[allowable_nones[stat_name]] == 0:
                    logging.info(f"Null value for stat: {stat_name} is allowable since corresponding count stat is 0; game: {game_name} for team {("home" if is_home else "away")}")
                    continue
                self.errors.append(f"Game {game_name} for team {("home" if is_home else "away")} has None value for stat: {stat_name}")
                continue
            if not isinstance(stat_value, (int, float)):
                self.errors.append(f"Game {game_name} for team {("home" if is_home else "away")} has non-numeric value for stat: {stat_name}: {stat_value}")
        if len(team_game_data) != len(self.stat_names): # + 2: # game_file and opponent are also expected fields)
            self.errors.append(f"Game {game_name} for team {("home" if is_home else "away")} has unexpected number of fields: {len(team_game_data)}; expected: {len(self.stat_names)}; data: {team_game_data}")


    def __get_all_games_for_team(self, team_name: str) -> list:
        year_games = self.team_game_data.get(team_name, None)
        if year_games is None:
            team_game_data = self.ifile_handler.load_team_file(team_name, True)
            if team_game_data is not None:
                year_games = team_game_data.get(self.year, None)
                if year_games is not None: # and len(year_games) > 0:
                    self.team_game_data[team_name] = year_games
        return year_games


    def __get_team_game_data(self, team_name: str, game_name: str) -> dict:
        week = Utils.get_week_from_file_name(game_name)
        if week is None:
            self.errors.append(f"Failed to extract week from game file name: {game_name}")
            return
        all_games = self.__get_all_games_for_team(team_name)
        if all_games is None:
            self.errors.append(f"Failed to load game data for team {team_name}; game_file: {game_name}")
            return
        if len(all_games) <= week:
            self.errors.append(f"Team {team_name} does not have a game for week {week} (number of games: {len(all_games)}) in year {self.year}; game_file: {game_name}")
            return
        team_game_data = all_games[week]
        if team_game_data is None:
            self.errors.append(f"Team {team_name} does not have a game data for year {self.year} / week {week}; game_file: {game_name}")
        return team_game_data


    def __add_update(self, team_name: str, updated_game: dict):
        if not self.do_fixes:
            return
        print(f"  ## Adding update for team {team_name}: {updated_game}")
        team_games = self.team_game_data.get(team_name, None)
        team_updates = self.updates[team_name] if team_name in self.updates else []
        week = Utils.get_week_from_file_name(updated_game["game_file"])
        Utils.add_element_to_list_at_index(team_updates, week, updated_game)
        self.updates[team_name] = team_updates


    def __save_updates(self):
        if not self.do_fixes:
            return
        for team, data in self.updates.items():
            print(f"Updating team file for team {team} for year {self.year}")
            self.ifile_handler.update_team_file(team, self.year, data, False)


    ### STATS CHECKS
    def __check_statistics(self):
        logging.info(f"Performing consistency check of stats files for year {self.year}...")
        all_stats_files = self.ifile_handler.get_all_averages_files(self.year)
        for stats_file in all_stats_files:
            logging.info(f"Checking stats file: {stats_file}")
            stats_data = self.ifile_handler.load_averages_file(self.year, stats_file)
            if stats_data is None:
                error_message  =f"Failed to load stats file: {stats_file}"
                logging.error(error_message)
                self.errors.append(error_message)
                continue
            team_stats = stats_data["team_stats"]
            if team_stats is None:
                error_message  =f"Failed to find team_stats in file {stats_file}"
                logging.error(error_message)
                self.errors.append(error_message)
                continue
            opp_stats = stats_data["opp_stats"]
            if opp_stats is None:
                error_message  =f"Failed to find opp_stats in file {stats_file}"
                logging.error(error_message)
                self.errors.append(error_message)
                continue

            logging.debug(f"Checking stats file: {stats_file}")
            self.__ensure_all_stats_present(stats_file, team_stats, True)
            self.__ensure_all_stats_present(stats_file, opp_stats, False)


    def __ensure_all_stats_present(self, stats_file: str, stats_data: dict, is_team: bool):
        # stat_names = Parse_Game_Data_File().get_stat_names()
        # stat_names.append("score")
        team = "team" if is_team else "opp"
        sub_fields = ["mean", "median", "stddev"]
        print(f"stats_data: {self.stat_names}")
        for stat_name in self.stat_names:
            for sub_field in sub_fields:
                field_name = stat_name + "_" + sub_field
                if field_name not in stats_data:
                    print(f"{field_name} not in stats_data.{team}")
                    self.errors.append(f"Stats file {stats_file} is missing expected field: {field_name} in {team} stats")
                else:
                    if stats_data[field_name] is None:
                        print(f"{field_name} not in stats_data.{team}")
                        self.errors.append(f"Stats file {stats_file} has null value for field: {field_name} in {team} stats")
        if len(stats_data) != len(self.stat_names) * len(sub_fields):
            self.errors.append(f"Stats file {stats_file} has unexpected number of fields: {len(stats_data)} in {team} stats; expected: {len(self.stat_names) * len(sub_fields)}") #"; data: {stats_data}")

        sdk = list(stats_data.keys())
        sn = self.stat_names
        sdk.sort()
        sn.sort()
        print("===============================")
        print(f"stats keys sorted: {sdk}")
        print("===============================")
        print(f"named stats sorted: {sn}")
