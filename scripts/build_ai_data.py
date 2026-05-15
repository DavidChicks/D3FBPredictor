

from curses import raw
import numpy as np
import tensorflow as tf
from ifile_handler import IFile_Handler
from parse_game_data_file import Parse_Game_Data_File
from sklearn.model_selection import train_test_split

EPOCHS = 10
TEST_SIZE = 0.2

class Build_AI_Data:
    def __init__(self, ifile_handler: IFile_Handler, year: int):
        self.ifile_handler = ifile_handler
        self.year = str(year)
        self.team_data = {}  # This will hold the team data: {"team_name": {"stat_name": value}}
        self.game_data = []  # This will hold the game data: {"away_team": str, "home_team": str, "away_score": int, "home_score": int}


    def build_ai_data(self):
        self.normalization_data  = self.__ensure_normailziation_file()
        # Implement logic to save the game data and normalization data as needed
        inputs, results = self.get_data_for_all_games()
        x_train, x_test, y_train, y_test = train_test_split(
            np.array(inputs), np.array(results), test_size=TEST_SIZE
        )

        model = self.__get_model()
        model.fit(x_train, y_train, epochs=EPOCHS)
        model.evaluate(x_test,  y_test, verbose=3)


    def get_data_for_all_games(self):
        all_games = self.ifile_handler.get_all_game_file_names(self.year)

        if (all_games is None or len(all_games) == 0):
            print("No game files found for year", self.year)
            return

        self.__get_model()
        inputs = []
        outputs = []
        for game_file_name in all_games:
            game_data = self.get_data_for_game(game_file_name)
            inputs.append(game_data["inputs"])
            outputs.append(game_data["result"])
            # print(f"Processed game file {game_file_name} for year {self.year}: game_data={game_data}")
            #self.__build_tensors(game_data)

        print(f"inputs[10]={inputs[10]}")
        print(f"outputs[10]={outputs[10]}")
        return inputs, outputs


    def get_data_for_game(self, game_file_name: str) -> dict:
        # Implement logic to extract data for a single game and apply normalization
        game_file_data = self.ifile_handler.load_game_file(self.year, game_file_name)
        #print(f"Loaded game file {game_file_name} for normalization: game_file_data={game_file_data}")
        game_data = {}
        home_team = game_file_data["home_team"]
        away_team = game_file_data["away_team"]
        game_data["home_score"] = game_file_data["home_score"]
        game_data["away_score"] = game_file_data["away_score"]
        #print(f"Processing game file {game_file_name}: home_team={home_team}, away_team={away_team}, home_score={game_data['home_score']}, away_score={game_data['away_score']}")
        game_data["inputs"] = []
        game_data["result"] = [
            #float(game_data["away_score"]) / 100.0, 
            #float(game_data["home_score"]) / 100.0,
            0.0 if game_data["away_score"] > game_data["home_score"] else 1.0 if game_data["away_score"] < game_data["home_score"] else .5
            ]

        if (self.team_data.get(away_team) is None):
            self.team_data[away_team] = self.ifile_handler.load_averages_file(self.year, away_team + ".json")
        if (self.team_data.get(home_team) is None):
            self.team_data[home_team] = self.ifile_handler.load_averages_file(self.year, home_team + ".json")
        away_stats = self.team_data[away_team]
        home_stats = self.team_data[home_team]
        if away_stats is None:
            print(f"Error: No team data found for away team {away_team} for year {self.year}")
            afoo = 1 / 0
        if home_stats is None:
            print(f"Error: No team data found for home team {home_team} for year {self.year}")
            hfoo = 1 / 0

        away_team_stats_normalized = []
        home_team_stats_normalized = []
        away_opp_stats_normalize = []
        home_opp_stats_normalize = []

        for stat_name in self.normalization_data.keys():
            away_team_stats_normalized.append(self.__normalize_stat(stat_name, away_stats["team_stats"][stat_name]))
            home_team_stats_normalized.append(self.__normalize_stat(stat_name, home_stats["team_stats"][stat_name]))
            away_opp_stats_normalize.append(self.__normalize_stat(stat_name, away_stats["opp_stats"][stat_name]))
            home_opp_stats_normalize.append(self.__normalize_stat(stat_name, home_stats["opp_stats"][stat_name]))

        game_data["inputs"].append(away_team_stats_normalized)
        game_data["inputs"].append(home_team_stats_normalized)
        game_data["inputs"].append(away_opp_stats_normalize)
        game_data["inputs"].append(home_opp_stats_normalize)
        return game_data


    def __ensure_normailziation_file(self):
        # Implement logic to ensure that the normalization file exists and is up to date
        normaillzation_data = self.ifile_handler.load_ai_normalization_file(self.year)
        if normaillzation_data is None:
            print("Normalization file not found for year", self.year)
            normaillzation_data = self.__generate_normailziation_file()
            self.ifile_handler.save_ai_normalization_file(self.year, normaillzation_data)
        else:
            print("Normalization file already exists for year", self.year)
        return normaillzation_data


    def __generate_normailziation_file(self):
        averages_files = self.ifile_handler.get_all_averages_files(self.year)
        # print(f"Found averages files for year {self.year} : {averages_files}")
        if averages_files is None or len(averages_files) == 0:
            print("No averages files found for year", self.year)
            return

        raw_stats = self.__get_all_stats_name()
        normalization = {}
        first_file = averages_files[0]
        first_data = self.ifile_handler.load_averages_file(self.year, first_file)
        #print(f"Loaded first averages file {first_file} for normalization: first_data={first_data}")
        for key in first_data["team_stats"].keys():
            stat_data = {
                "min": first_data["team_stats"][key],
                "max": first_data["team_stats"][key]}
            normalization[key] = stat_data

        for averages_file in averages_files:
            data = self.ifile_handler.load_averages_file(self.year, averages_file)
            for team_stats_name in ["team_stats", "opp_stats"]:
                #print (f"Processing {averages_file} for normalization: team_stats_name={team_stats_name}, data={data[team_stats_name]}")
                for key in data[team_stats_name].keys():
                    if key in normalization:
                        normalization[key]["min"] = min(normalization[key]["min"], data[team_stats_name][key])
                        normalization[key]["max"] = max(normalization[key]["max"], data[team_stats_name][key])
                        if (data[team_stats_name][key] == 0):
                            print(f"Found zero value: {key} in {team_stats_name} of file {averages_file}")
                    else:
                        normalization[key] = {"min": data[key], "max": data[key]}
        return normalization


    def __get_all_stats_name() -> list:
        stats_name = Parse_Game_Data_File.stat_rename()
        stats_name.append("score")

        all_statistical_stats = []
        for stat in stats_name:
            all_statistical_stats.append(stat + "_mean")
            all_statistical_stats.append(stat + "_median")
            all_statistical_stats.append(stat + "_stddev")
        return all_statistical_stats


    def __normalize_stat(self, stat_name: str, value: float) -> float:
        return (value - self.normalization_data[stat_name]["min"]) / (self.normalization_data[stat_name]["max"] - self.normalization_data[stat_name]["min"])


    #def __build_tensors(self, game_data: dict):
    #    data_as_arrays = []
    #    print("home_team_stats_normalized length: ", len(game_data["home_team_stats_normalized"]))
    #    print("home_opp_stats_normalize length: ", len(game_data["home_opp_stats_normalize"]))
    #    print("away_opp_stats_normalize length: ", len(game_data["away_opp_stats_normalize"]))
    #    print("home_team_stats_normalized length: ", len(game_data["home_team_stats_normalized"]))
    #
    #    data_as_arrays.append(game_data["home_team_stats_normalized"])
    #    data_as_arrays.append(game_data["home_team_stats_normalized"])
    #    data_as_arrays.append(game_data["away_opp_stats_normalize"])
    #    data_as_arrays.append(game_data["home_opp_stats_normalize"])



    def __get_model(self):
        """
        Returns a compiled convolutional neural network model. Assume that the
        `input_shape` of the first layer is `(IMG_WIDTH, IMG_HEIGHT, 3)`.
        The output layer should have `NUM_CATEGORIES` units, one for each category.
        """
        # MUST FLATTEN TO USE SEQUENTIAL MODEL
        model = tf.keras.models.Sequential()
        model.add(tf.keras.layers.Flatten())

        model.add(tf.keras.layers.Dense(256, activation="relu"))
        # model.add(tf.keras.layers.Dense(128, activation="relu"))
        model.add(tf.keras.layers.Dense(256, activation="tanh"))
        model.add(tf.keras.layers.Dropout(.5))
        model.add(tf.keras.layers.Dense(256, activation="elu"))
        model.add(tf.keras.layers.Dropout(.5))
        model.add(tf.keras.layers.Dense(256, activation="relu"))
        model.add(tf.keras.layers.Dense(1, activation="sigmoid"))

        #loss_fn = tf.keras.losses.Loss(name=None, reduction='sum_over_batch_size', dtype=None)
        oprimizer = tf.keras.optimizers.Adam(learning_rate=0.02)
        # model.compile(loss=loss_fn, optimizer=oprimizer, metrics=["accuracy"])
        # model.compile(loss="binary_crossentropy", optimizer="adam", metrics=["accuracy"])
        model.compile(loss="mean_squared_error", optimizer="adam", metrics=["accuracy"])

        return model


        #inputs = tf.keras.Input(shape=(117,))
