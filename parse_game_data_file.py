"""Fetch https://www.d3football.com/teams/index and prepare it for parsing.

Usage:
  python get_teams.py         # fetch and save to data/teams_index.html (uses cache)
  python get_teams.py --force # re-fetch and overwrite
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import pprint
import re
import requests
from typing import Optional

from bs4 import BeautifulSoup

URL_ROOT = "https://www.d3football.com/"
URL = "https://www.d3football.com/teams/index"
DEFAULT_SAVE_PATH = os.path.join("data", "teams_index.html")


class Parse_Game_Data_File:
    # keys for stat splitting rules
    stat_splitter_ignore_fields = "stat_splitter_ignore_fields"
    stat_splitter_type = "stat_splitter_type"
    stat_splitter_type_split = "stat_splitter_type_split"
    stat_splitter_type_percent = "stat_splitter_type_percent"
    stat_splitter_key_prepend = "prepend"
    stat_splitter_key_postpend = "postpend"
    stat_splitter_key_postremove = "postremove"
    stat_splitter_percentage = "stat_splitter_percentage"
    stat_splitter_key_success = "stat_splitter_key_success"
    stat_splitter_field_splitter = "stat_splitter_field_splitter"
    stat_spliiter_expectted_fields_count = "stat_spliiter_expectted_fields_count"
    stat_splitter_field_splitter_field_header_determiner = "stat_splitter_field_splitter_field_header_determiner"

    stat_sub_splitter = "stat_sub_splitter"
    stat_splitter = {
        "PassingRushingPenalty": {
            stat_splitter_type: stat_splitter_type_split,
            stat_splitter_ignore_fields: "<br/>",
            stat_splitter_key_prepend: "First Down by ",
            stat_splitter_field_splitter: None,
            stat_splitter_field_splitter_field_header_determiner: None,
            stat_spliiter_expectted_fields_count: 3
            },
        "THIRD DOWN EFFICIENCY": {
            stat_splitter_type: stat_splitter_type_percent,
            stat_splitter_key_postremove: " EFFICIENCY",
            stat_splitter_key_success: " Conversions",
            stat_splitter_field_splitter_field_header_determiner: None
            },
        "FOURTH DOWN EFFICIENCY": {
            stat_splitter_type: stat_splitter_type_percent,
            stat_splitter_key_postremove: " EFFICIENCY",
            stat_splitter_key_success: " Conversions",
            stat_splitter_field_splitter_field_header_determiner: None
            },
        "Total Offensive PlaysAverage gain per play": {
            stat_splitter_type: stat_splitter_type_split,
            stat_splitter_ignore_fields: "<br/>",
            stat_splitter_key_prepend: None,
            stat_splitter_field_splitter: None,
            stat_splitter_field_splitter_field_header_determiner: None,
            stat_spliiter_expectted_fields_count: 2
            },
        "PUNTS: Number-Yards": {
            stat_splitter_type: stat_splitter_type_split,
            stat_splitter_ignore_fields: None,
            stat_splitter_key_prepend: None,
            stat_splitter_field_splitter: "-",
            stat_splitter_field_splitter_field_header_determiner: ": ",
            stat_spliiter_expectted_fields_count: 2
            },
        "SACKS: Number-Yards": {
            stat_splitter_type: stat_splitter_type_split,
            stat_splitter_ignore_fields: None,
            stat_splitter_key_prepend: None,
            stat_splitter_field_splitter: "-",
            stat_splitter_field_splitter_field_header_determiner: ": ",
            stat_spliiter_expectted_fields_count: 2
            },
        "PENALTIES: Number-Yards": {
            stat_splitter_type: stat_splitter_type_split,
            stat_splitter_ignore_fields: None,
            stat_splitter_key_prepend: None,
            stat_splitter_field_splitter: "-",
            stat_splitter_field_splitter_field_header_determiner: ": ",
            stat_spliiter_expectted_fields_count: 2
            },
        "FUMBLES: Number-Lost": {
            stat_splitter_type: stat_splitter_type_split,
            stat_splitter_ignore_fields: None,
            stat_splitter_key_prepend: None,
            stat_splitter_field_splitter: "-",
            stat_splitter_field_splitter_field_header_determiner: ": ",
            stat_spliiter_expectted_fields_count: 2
            },
        "INTERCEPTIONS: Number-Yards": {    # does this work if yars is negative??
            stat_splitter_type: stat_splitter_type_split,
            stat_splitter_ignore_fields: None,
            stat_splitter_key_prepend: None,
            stat_splitter_field_splitter: "-",
            stat_splitter_field_splitter_field_header_determiner: ": ",
            stat_spliiter_expectted_fields_count: 2
            },
        "Rushing AttemptsAverage gain per rush": {
            stat_splitter_type: stat_splitter_type_split,
            stat_splitter_ignore_fields: "<br/>",
            stat_splitter_key_prepend: None,
            stat_splitter_field_splitter: None,
            stat_splitter_field_splitter_field_header_determiner: None,
            stat_spliiter_expectted_fields_count: 2
            },
        "Completions-AttemptsNet yards per pass playSacked: Number-YardsHad intercepted": {
            stat_splitter_type: stat_splitter_type_split,
            stat_splitter_ignore_fields: "<br/>",
            stat_splitter_key_prepend: None,
            stat_splitter_field_splitter: None,
            stat_splitter_field_splitter_field_header_determiner: None,
            stat_spliiter_expectted_fields_count: 4
            },
        "Punt Returns: Number-YardsKickoff Returns: Number-YardsInterception Returns: Number-Yards": {
            stat_splitter_type: stat_splitter_type_split,
            stat_splitter_ignore_fields: "<br/>",
            stat_splitter_key_prepend: None,
            stat_splitter_field_splitter: "-",
            stat_splitter_field_splitter_field_header_determiner: ": ",
            stat_spliiter_expectted_fields_count: 6
            },
        "Completions-AttemptsNet yards per pass playSacked: Number-YardsHad intercepted": {
            stat_splitter_type: stat_splitter_type_split,
            stat_splitter_ignore_fields: "<br/>",
            stat_splitter_key_prepend: None,
            stat_splitter_field_splitter: "-",
            stat_splitter_field_splitter_field_header_determiner: None,
            stat_spliiter_expectted_fields_count: 6
            }

    }


    def get_child_fields(self, cell: dict, ignore_fields:str, strip: bool) -> list[str]:
        children = []
        for sub_cell in cell.children:
            if ignore_fields is not None and str(sub_cell) == ignore_fields:
                continue
            children.append(sub_cell.get_text(strip=strip) if hasattr(sub_cell, "get_text") else str(sub_cell))
        if len(children) == 0:
            children.append(cell.get_text(strip=strip) if hasattr(cell, "get_text") else str(cell))
        return children


    def get_child_parts_non_empty(self, child: str, sub_field_splitter: str) -> list[str]:
        parts = child.split(sub_field_splitter)
        empty_string_index = parts.index("") if "" in parts else None
        if empty_string_index is not None:
            parts.pop(empty_string_index)
            if len(parts) > empty_string_index:
                parts[empty_string_index] = sub_field_splitter + parts[empty_string_index]
        return parts;


    def get_sub_fields(self, cell, sub_field_splitter: str, ignore_fields: str, determiner: str, expected_parts_count: int) -> list[str]:
        fields = []
        children = self.get_child_fields(cell, ignore_fields, strip=True)

        for child in children:
            if sub_field_splitter is not None and sub_field_splitter in child:
                parts = self.get_child_parts_non_empty(child, sub_field_splitter)
                if determiner is not None:
                    parts = self.fix_field_names2(parts, determiner)
                fields.extend(parts)
            else:
                fields.append(child)
        if len(fields) != expected_parts_count:
            print(f"!!! Incorrect split count in cell for stat {cell} (expected {expected_parts_count} but got {len(fields)}) !!!")
            return None
        return fields


    def get_percentage_parts(self, cell) -> list[str]:
        text = cell.get_text(strip=True) if hasattr(cell, "get_text") else str(cell)
        nums = re.findall(r"\d+", text)
        if len(nums) >= 2:
            return [
                nums[-2],
                nums[-1],
                str(int(nums[-2])/int(nums[-1])) if (nums[-1] != "0") else "0"
            ]
        return []


    def fix_field_names(self, field_names: list[str], stat_splitting) -> list[str]:
        if stat_splitting[self.stat_splitter_field_splitter_field_header_determiner] is None:
            return field_names
        determiner = stat_splitting[self.stat_splitter_field_splitter_field_header_determiner]
        field_header = None
        for field_name in field_names:
            if determiner in field_name:
                parts = field_name.split(determiner)
                field_header = parts[0]
                break
        if field_header is None:
            return field_names
        field_names = [
                (field_header + determiner + field_name if not field_name.startswith(field_header) else field_name)
                for field_name in field_names
                ]
        return field_names


    def fix_field_names2(self, field_names: list[str], determiner: str) -> list[str]:
        field_header = None
        for field_name in field_names:
            if determiner in field_name:
                parts = field_name.split(determiner)
                field_header = parts[0]
                break
        if field_header is None:
            return field_names
        field_names = [
                (field_header + determiner + field_name if not field_name.startswith(field_header) else field_name)
                for field_name in field_names
                ]
        return field_names


    def get_percentage_fields(self, away_stats: list[str], home_stats: list[str], stat_splitting: dict, cells) -> None:
        cell_type = type(cells[0])
        name = cells[1].get_text(strip=True)
        if self.stat_splitter_key_postremove in stat_splitting:
            name = name.replace(stat_splitting[self.stat_splitter_key_postremove], "")
        name = name.strip()
        values_away = self.get_percentage_parts(cells[0])
        values_home = self.get_percentage_parts(cells[2])
        away_stats[name + stat_splitting[self.stat_splitter_key_success]] = values_away[0]
        home_stats[name + stat_splitting[self.stat_splitter_key_success]] = values_home[0]
        away_stats[name + " Total"] = values_away[1]
        home_stats[name + " Total"] = values_home[1]
        away_stats[name + stat_splitting[self.stat_splitter_key_postremove]] = values_away[2]
        home_stats[name + stat_splitting[self.stat_splitter_key_postremove]] = values_home[2]


    def get_separted_fields(self, stat_splitting: dict, cells): # -> list[str], list[str], list[str]:
        expectted_fields_count = stat_splitting[self.stat_spliiter_expectted_fields_count]
        field_names = self.get_sub_fields(cells[1], 
                                        stat_splitting[self.stat_splitter_field_splitter],
                                        stat_splitting[self.stat_splitter_ignore_fields],
                                        stat_splitting[self.stat_splitter_field_splitter_field_header_determiner],
                                        expectted_fields_count)
        print(f"    Got field names: {field_names}")
        print(f"    Got field names: {field_names}")

        print(f"    !! field_names: {field_names}")
        away_sub_stats = self.get_sub_fields(cells[0],
                                        stat_splitting[self.stat_splitter_field_splitter],
                                        stat_splitting[self.stat_splitter_ignore_fields],
                                        None,
                                        expectted_fields_count)
        home_sub_stats = self.get_sub_fields(cells[2],
                                        stat_splitting[self.stat_splitter_field_splitter],
                                        stat_splitting[self.stat_splitter_ignore_fields],
                                        None,
                                        expectted_fields_count)
        return field_names, away_sub_stats, home_sub_stats




    def update_field_names(self, field_names: list[str], stat_splitting) -> list[str]:
        if stat_splitting[self.stat_splitter_field_splitter_field_header_determiner] is not None:
            determiner = stat_splitting[self.stat_splitter_field_splitter_field_header_determiner]
            field_header = None
            for field_name in field_names:
                if field_name.startswith(determiner):
                    field_header = field_name
                    break
            if field_header is not None:
                for field_name in field_names:
                    if not field_name.startswith(determiner):
                        field_name = field_header + determiner + field_name
        return field_names


    def get_game_stats(self, game_stats_table) -> Optional[dict]:
        #teams_table = game_page.find_all("table", class_="all-center")
        #if teams_table is None or len(teams_table) == 0:
        #    print("  Failed to find teams info table on game page.")
        #    return None
        home_stats = {}
        away_stats = {}
        rows = game_stats_table.find_all("tr")
        team_name_row = rows[0]
        team_names = team_name_row.find_all("th")
        team_away = team_names[0].get_text(strip=True)
        team_home = team_names[2].get_text(strip=True)

        for row in rows:
            print(f"  Processing row")
            # get the first anchor in the row
            cells = row.find_all("td")
            for cell in cells:
                print(f"    Processing cell: {cell.get_text(strip="True")}")
            if len(cells) != 3:
                print(f"     Incorrect cell count in row ({len(cells)}), skipping")
                continue

            stat = cells[1].get_text(strip=True)
            if stat in self.stat_splitter:
                print(f"  Found stat with special splitting rules: {stat}")
                stat_spliting = self.stat_splitter[stat]
                field_names = []
                away_sub_stats = []
                home_sub_stats = []
                if stat_spliting[self.stat_splitter_type] == self.stat_splitter_type_percent:
                    self.get_percentage_fields(away_stats, home_stats, stat_spliting, cells)
                else:  # stat_splitter_type_split
                    field_names, away_sub_stats, home_sub_stats = self.get_separted_fields(stat_spliting, cells)
                    if stat_spliting[self.stat_splitter_field_splitter] is None:
                        field_names = self.fix_field_names(field_names, stat_spliting)
                pprint.pp(f"    field_names: {field_names}")

                if field_names is None or away_sub_stats is None or home_sub_stats is None:
                    print(f"     Incorrect split count in row for stat {stat} (fields={len(field_names)}, away_stats={len(away_stats)}, home_stats={len(home_stats)}), skipping")
                    continue

                for i, field_name in enumerate(field_names):
                    away_stats[field_name] = away_sub_stats[i]
                    home_stats[field_name] = home_sub_stats[i]

            else:
                away_stats[stat] = cells[0].get_text(strip=True)
                home_stats[stat] = cells[2].get_text(strip=True)

        return_object = {}
        return_object["away_name"] = team_away
        return_object["home_name"] = team_home
        return_object["away_stats"] = away_stats
        return_object["home_stats"] = home_stats
        return return_object


