from __future__ import annotations

from curses import raw
import logging
import numpy as np
import tensorflow as tf
from iall_teams import IAll_Teams
from ifile_handler import IFile_Handler
from parse_game_data_file import Parse_Game_Data_File
from sklearn.model_selection import train_test_split

DATA_SET_SIZE = 468 # 117 stats for each team and opp, so 117 * 4 = 468
EPOCHS = 100
TEST_SIZE = 0.2

class Build_AI_Data:
    def __init__(self, ifile_handler: IFile_Handler, iall_teams: IAll_Teams):
        self.ifile_handler = ifile_handler
        self.iall_teams = iall_teams
        self.team_data = {}  # This will hold the team data: {"team_name": {"stat_name": value}}
        self.game_data = []  # This will hold the game data: {"away_team": str, "home_team": str, "away_score": int, "home_score": int}
        self.errors = []


    def build_ai_data(self):
        all_inputs = []
        all_results = []
        years = self.ifile_handler.get_all_game_years()
        for year in years:
            logging.info("Loading data for year: " + year)

            if len(self.ifile_handler.get_all_averages_files(year)) == 0:
                logging.info(f"  No averagees file found for year, {year}, skipping")
                continue

            self.normalization_data  = self.__ensure_normailziation_file(year)
            # Implement logic to save the game data and normalization data as needed

            year_inputs, year_results = self.__get_data_for_all_games(year)
            all_inputs.extend(year_inputs)
            all_results.extend(year_results)
            print(f"inputs count for year {year}: {len(year_inputs)}")
            print(f"results count for year {year}: {len(year_results)}")

        print(f"inputs count: {len(all_inputs)}")
        print(f"results count: {len(all_results)}")

        try:
            x_train, x_test, y_train, y_test = train_test_split(
                np.array(all_inputs), np.array(all_results), test_size=TEST_SIZE
            )

            model = self.__get_model()
            model.fit(x_train, y_train, epochs=EPOCHS)
            model.evaluate(x_test,  y_test, verbose=3)
        except Exception as e:
            logging.error(f"Exception during model training/evaluation: {e}")
            self.errors.append(f"Exception during model training/evaluation: {e}")
            # raise e
        if len(self.errors) > 0:
            logging.error(f"Errors encountered during data processing:")
            for error in self.errors:
                logging.error(f"  {error}")


    def __get_data_for_all_games(self, year):
        logging.info(f"Loading game files from year {year}")
        all_games = self.ifile_handler.get_all_game_file_names(year)

        if (all_games is None or len(all_games) == 0):
            logging.warning(f"No game files found for year, {year}")
            return

        self.__get_model()
        inputs = []
        outputs = []
        for game_file_name in all_games:
            game_data = self.__get_data_for_game(game_file_name, year)
            if game_data is None:
                logging.warning(f"  Failed to process game file {game_file_name} for year {year}, skipping")
                continue
            inputs.append(game_data["inputs"])
            outputs.append(game_data["result"])
        logging.info(f"  Processed {len(all_games)} game files")
        return inputs, outputs


    def __get_data_for_game(self, game_file_name: str, year: str) -> dict:
        game_file_data = self.ifile_handler.load_game_file(year, game_file_name)
        game_data = {}
        home_team = self.iall_teams.get_primary_team_name(game_file_data["home_team"])
        away_team = self.iall_teams.get_primary_team_name(game_file_data["away_team"])
        game_data["home_score"] = game_file_data["home_score"]
        game_data["away_score"] = game_file_data["away_score"]
        game_data["inputs"] = []
        game_data["result"] = [
            #float(game_data["away_score"]) / 100.0, 
            #float(game_data["home_score"]) / 100.0,
            0.0 if game_data["away_score"] > game_data["home_score"] else 1.0 if game_data["away_score"] < game_data["home_score"] else .5
            ]

        if (self.team_data.get(away_team) is None):
            self.team_data[away_team] = self.ifile_handler.load_averages_file(year, away_team + ".json")
        if (self.team_data.get(home_team) is None):
            self.team_data[home_team] = self.ifile_handler.load_averages_file(year, home_team + ".json")
        away_stats = self.team_data[away_team]
        home_stats = self.team_data[home_team]
        if away_stats is None:
            logging.error(f"Error: No team data found for away team {away_team} for year {year}")
            return None
        if home_stats is None:
            logging.error(f"Error: No team data found for home team {home_team} for year {year}")
            return None

        away_team_stats_normalized = []
        home_team_stats_normalized = []
        away_opp_stats_normalize = []
        home_opp_stats_normalize = []

        for stat_name in self.normalization_data.keys():
            away_team_stats_normalized.append(self.__normalize_stat(stat_name, away_stats["team_stats"][stat_name]))
            home_team_stats_normalized.append(self.__normalize_stat(stat_name, home_stats["team_stats"][stat_name]))
            away_opp_stats_normalize.append(self.__normalize_stat(stat_name, away_stats["opp_stats"][stat_name]))
            home_opp_stats_normalize.append(self.__normalize_stat(stat_name, home_stats["opp_stats"][stat_name]))

        game_data["inputs"].extend(away_team_stats_normalized)
        game_data["inputs"].extend(home_team_stats_normalized)
        game_data["inputs"].extend(away_opp_stats_normalize)
        game_data["inputs"].extend(home_opp_stats_normalize)
        data_set_size = len(game_data["inputs"])
        if data_set_size != DATA_SET_SIZE:
            error_message = f"Unexpected size of inputs for game file {game_file_name}: {data_set_size} (expected {DATA_SET_SIZE})"
            logging.error(error_message)
            self.errors.append(error_message)
        return game_data


    def __ensure_normailziation_file(self, year: str):
        # Implement logic to ensure that the normalization file exists and is up to date
        normaillzation_data = self.ifile_handler.load_ai_normalization_file(year)
        if normaillzation_data is None:
            logging.info(f"Normalization file not found for year {year}")
            normaillzation_data = self.__generate_normailziation_file(year)
            self.ifile_handler.save_ai_normalization_file(year, normaillzation_data)
        else:
            logging.info(f"Normalization file already exists for year {year}")
        return normaillzation_data


    def __generate_normailziation_file(self, year: str):
        averages_files = self.ifile_handler.get_all_averages_files(year)
        if averages_files is None or len(averages_files) == 0:
            logging.info(f"No averages files found for year {year}")
            return

        raw_stats = self.__get_all_stats_name()
        normalization = {}
        first_file = averages_files[0]
        first_data = self.ifile_handler.load_averages_file(year, first_file)
        for key in first_data["team_stats"].keys():
            stat_data = {
                "min": first_data["team_stats"][key],
                "max": first_data["team_stats"][key]}
            normalization[key] = stat_data

        for averages_file in averages_files:
            data = self.ifile_handler.load_averages_file(year, averages_file)
            for team_stats_name in ["team_stats", "opp_stats"]:
                for key in data[team_stats_name].keys():
                    if key in normalization:
                        try:
                            normalization[key]["min"] = min(normalization[key]["min"], data[team_stats_name][key])
                            normalization[key]["max"] = max(normalization[key]["max"], data[team_stats_name][key])
                        except Exception as e:
                            logging.error(f"Execption e: {e}")
                            logging.error(f"  key: {key}")
                            logging.error(f"    data: {data[team_stats_name][key]}")
                            raise e
                    else:
                        normalization[key] = {"min": data[key], "max": data[key]}
        return normalization


    def __get_all_stats_name(self) -> list:
        stats_name = Parse_Game_Data_File.get_stat_names()
        stats_name.append("score")
        all_statistical_stats = []
        for stat in stats_name:
            all_statistical_stats.append(stat + "_mean")
            all_statistical_stats.append(stat + "_median")
            all_statistical_stats.append(stat + "_stddev")
        return all_statistical_stats


    def __normalize_stat(self, stat_name: str, value: float) -> float:
        return (value - self.normalization_data[stat_name]["min"]) / (self.normalization_data[stat_name]["max"] - self.normalization_data[stat_name]["min"])


    def __get_model(self):
        """
        Returns a compiled convolutional neural network model. Assume that the
        `input_shape` of the first layer is `(IMG_WIDTH, IMG_HEIGHT, 3)`.
        The output layer should have `NUM_CATEGORIES` units, one for each category.
        """
        # MUST FLATTEN TO USE SEQUENTIAL MODEL
        model = tf.keras.models.Sequential()
        #inputs = tf.keras.Input(shape=(DATA_SET_SIZE,))

        #model.add(tf.keras.layers.Flatten())

        model.add(tf.keras.layers.Dense(512, activation="relu", input_shape=(DATA_SET_SIZE,)))
        # model.add(tf.keras.layers.Dense(128, activation="relu"))
        model.add(tf.keras.layers.Dense(256, activation="relu"))
        model.add(tf.keras.layers.Dropout(.2))
        model.add(tf.keras.layers.Dense(512, activation="relu"))
        #model.add(tf.keras.layers.Dropout(.3))
        model.add(tf.keras.layers.Dense(256, activation="relu"))
        #model.add(tf.keras.layers.Dense(1, activation="sigmoid"))

        model.add(tf.keras.layers.Dense(512, activation="relu"))
        model.add(tf.keras.layers.Dense(512, activation="relu"))
        model.add(tf.keras.layers.Dropout(.3))
        model.add(tf.keras.layers.Dense(512, activation="relu"))

        #loss_fn = tf.keras.losses.Loss(name=None, reduction='sum_over_batch_size', dtype=None)
        # oprimizer = tf.keras.optimizers.Adam(learning_rate=0.02)
        # model.compile(loss=loss_fn, optimizer=oprimizer, metrics=["accuracy"])
        # model.compile(loss="binary_crossentropy", optimizer="adam", metrics=["accuracy"])
        model.add(tf.keras.layers.Dense(1, activation="sigmoid"))
        model.compile(loss="binary_crossentropy", optimizer="adam", metrics=["accuracy"])

        return model


        #inputs = tf.keras.Input(shape=(DATA_SET_SIZE,))
