"""Game statistics container.

This class behaves like a mapping (dict) but also allows attribute-style access.
It subclasses `dict` so it is JSON-serializable by the standard `json` module.
"""

from __future__ import annotations

from typing import Any


class Game_Statistics(dict):
    """Dictionary-like container for game statistics with attribute access.

    Example:
        gs = Game_Statistics()
        gs.First_downs_total = 12
        print(gs["First_downs_total"])  # 12
        json.dumps(gs)  # works because it's a dict subclass
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __setattr__(self, name: str, value: Any) -> None:
        # Map attribute set to dict item, unless it's a private attribute
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self[name] = value

    def __getattr__(self, name: str) -> Any:
        # Provide attribute access for keys present in the dict
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(name) from e

    def to_dict(self) -> dict:
        return dict(self)

    def __repr__(self) -> str:
        return f"Game_Statistics({super().__repr__()})"

    # Optional mapping of field name -> expected type. This can be used by callers
    # to determine how to coerce values when populating statistics.
    field_types = {
        "First_downs_total": int,
        "First_downs_passing": int,
        "First_downs_rushing": int,
        "First_downs_penalties": int,
        "Third_down_conversions": int,
        "Third_downs_count": int,
        "Third_downs_efficiency": float,
        "Fourth_downs_conversions": int,
        "Fourth_downs_count": int,
        "Fourth_downs_efficiency": float,
        "Offensive_yards": int,
        "Offensive_plays": int,
        "Offensive_yards_per_play": float,
        "Pass_yards": int,
        "Pass_completions": int,
        "Pass_plays": int,
        "Pass_yards_per_play": float,
        "Sacks_count": int,
        "Sacks_yards": int,
        "Int_thrown": int,
        "Rush_yards": int,
        "Rush_plays": int,
        "Rush_yards_per_play": float,
        "Punts_count": int,
        "Punts_yards": int,
        "Punts_yards_average": float,
        "Return_yards_total": int,
        "Punt_ret_count": int,
        "Punt_ret_yards": int,
        "KO_ret_count": int,
        "KO_ret_yards": int,
        "Int_ret_count": int,
        "Int_ret_yards": int,
        "Pentalies_count": int,
        "Penalties_yards": int,
        "Fumbles_count": int,
        "Fumbles_lost": int,
        "Int_ret_yard": int,
        "TOP": int,
    }

    #First_downs_total: int
    #First_downs_passing: int
    #First_downs_rushing: int
    #First_downs_penalties: int
    #Third_down_conversions: int
    #Third_downs_count: int
    #Third_downs_efficiency: float
    #Fourth_downs_conversions: int
    #Fourth_downs_count: int
    #Fourth_downs_efficiency: float
    #Yards_total: int
    #Offensive_plays: int
    #Yards_per_play: float
    #Pass_yards: int
    #Pass_completions: int
    #Pass_attempts: int
    #Pass_yards_average: float
    #Sacks_count: int
    #Sacks_yards: int
    #Int_thrown: int
    #Rush_yards: int
    #Rush_attempts: int
    #Rush_yards_average: float
    #Punts_count: int
    #Punts_yards: int
    #Punts_yards_average: float
    #Return_yards_total: int
    #Punt_ret_count: int
    #Punt_ret_yards: int
    #KO_ret_count: int
    #KO_ret_yards: int
    #Int_ret_count: int
    #Int_ret_yards: int
    #Pentalies_count: int
    #Penalties_yards: int
    #Fumbles_count: int
    #Fumbles_lost: int
    #Sacks_count: int
    #Sacks_yards: int
    #Int_ret_count: int
    #Int_ret_yard: int
    #TOP: int