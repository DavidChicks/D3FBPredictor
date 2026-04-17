"""Fetch https://www.d3football.com/teams/index and prepare it for parsing.

Usage:
  python parse_game_data_file.get_game_stats()
  python parse_game_data_file.get_game_score
"""
from __future__ import annotations
from typing import Optional
from utils import Utils
import re


class Parse_Game_Data_File:
    away_team: str
    home_team: str

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
        "INTERCEPTIONS: Number-Yards": {
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


    def __get_child_fields(self, cell: dict, ignore_fields:str, strip: bool) -> list[str]:
        children = []
        for sub_cell in cell.children:
            if ignore_fields is not None and str(sub_cell) == ignore_fields:
                continue
            children.append(sub_cell.get_text(strip=strip) if hasattr(sub_cell, "get_text") else str(sub_cell))
        if len(children) == 0:
            children.append(cell.get_text(strip=strip) if hasattr(cell, "get_text") else str(cell))
        return children


    def __get_child_parts_non_empty(self, child: str, sub_field_splitter: str) -> list[str]:
        parts = child.split(sub_field_splitter)
        empty_string_index = parts.index("") if "" in parts else None
        if empty_string_index is not None:
            parts.pop(empty_string_index)
            if len(parts) > empty_string_index:
                parts[empty_string_index] = sub_field_splitter + parts[empty_string_index]
        return parts;


    def __get_sub_fields(self, cell, sub_field_splitter: str, ignore_fields: str, determiner: str, expected_parts_count: int) -> list[str]:
        fields = []
        children = self.__get_child_fields(cell, ignore_fields, strip=True)

        for child in children:
            if "0  0" in child: # handle cases where the number/yards is "0  0" rather than "0-0"
                #print(f"  ## found '0  0': '{child}'")
                child = "0-0"
            if sub_field_splitter is not None and sub_field_splitter in child:
                parts = self.__get_child_parts_non_empty(child, sub_field_splitter)
                if determiner is not None:
                    parts = self.__fix_field_names2(parts, determiner)
                fields.extend(parts)
            else:
                fields.append(child)
        if len(fields) != expected_parts_count:
            print(f"!!! Incorrect split count in cell for stat {cell} (expected {expected_parts_count} but got {len(fields)}) !!!")
            print(f"    Away Team: {self.away_team}, Home Team: {self.home_team}")
            return None
        return fields


    def __get_percentage_parts(self, cell) -> list[str]:
        text = cell.get_text(strip=True) if hasattr(cell, "get_text") else str(cell)
        nums = re.findall(r"\d+", text)
        if len(nums) >= 2:
            return [
                nums[-2],
                nums[-1],
                str(int(nums[-2])/int(nums[-1])) if (nums[-1] != "0") else "0"
            ]
        return []


    def __fix_field_names(self, field_names: list[str], stat_splitting) -> list[str]:
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


    def __fix_field_names2(self, field_names: list[str], determiner: str) -> list[str]:
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


    def __get_percentage_fields(self, away_stats: list[str], home_stats: list[str], stat_splitting: dict, cells) -> None:
        cell_type = type(cells[0])
        name = cells[1].get_text(strip=True)
        if self.stat_splitter_key_postremove in stat_splitting:
            name = name.replace(stat_splitting[self.stat_splitter_key_postremove], "")
        name = name.strip()
        values_away = self.__get_percentage_parts(cells[0])
        values_home = self.__get_percentage_parts(cells[2])
        away_stats[name + stat_splitting[self.stat_splitter_key_success]] = values_away[0]
        home_stats[name + stat_splitting[self.stat_splitter_key_success]] = values_home[0]
        away_stats[name + " Total"] = values_away[1]
        home_stats[name + " Total"] = values_home[1]
        away_stats[name + stat_splitting[self.stat_splitter_key_postremove]] = values_away[2]
        home_stats[name + stat_splitting[self.stat_splitter_key_postremove]] = values_home[2]


    def __get_separted_fields(self, stat_splitting: dict, cells): # -> list[str], list[str], list[str]:
        expectted_fields_count = stat_splitting[self.stat_spliiter_expectted_fields_count]
        field_names = self.__get_sub_fields(cells[1], 
                                        stat_splitting[self.stat_splitter_field_splitter],
                                        stat_splitting[self.stat_splitter_ignore_fields],
                                        stat_splitting[self.stat_splitter_field_splitter_field_header_determiner],
                                        expectted_fields_count)
        away_sub_stats = self.__get_sub_fields(cells[0],
                                        stat_splitting[self.stat_splitter_field_splitter],
                                        stat_splitting[self.stat_splitter_ignore_fields],
                                        None,
                                        expectted_fields_count)
        home_sub_stats = self.__get_sub_fields(cells[2],
                                        stat_splitting[self.stat_splitter_field_splitter],
                                        stat_splitting[self.stat_splitter_ignore_fields],
                                        None,
                                        expectted_fields_count)
        return field_names, away_sub_stats, home_sub_stats


    def __process_row(self, row, away_stats, home_stats) -> None:
        cells = row.find_all("td")
        if len(cells) != 3:
            if not "Statistics" in row.get_text():
                print(f"     Incorrect cell count in row ({len(cells)}) of row {row}, skipping")
            return

        stat = cells[1].get_text(strip=True)
        if stat in self.stat_splitter:
            stat_spliting = self.stat_splitter[stat]
            field_names = []
            away_sub_stats = []
            home_sub_stats = []
            if stat_spliting[self.stat_splitter_type] == self.stat_splitter_type_percent:
                self.__get_percentage_fields(away_stats, home_stats, stat_spliting, cells)
            else:  # stat_splitter_type_split
                field_names, away_sub_stats, home_sub_stats = self.__get_separted_fields(stat_spliting, cells)
                if stat_spliting[self.stat_splitter_field_splitter] is None:
                    field_names = self.__fix_field_names(field_names, stat_spliting)

            if field_names is None or away_sub_stats is None or home_sub_stats is None:
                return

            for i, field_name in enumerate(field_names):
                away_stats[field_name] = away_sub_stats[i]
                home_stats[field_name] = home_sub_stats[i]

        else:
            away_stats[stat] = cells[0].get_text(strip=True)
            home_stats[stat] = cells[2].get_text(strip=True)


    def __get_score_from_td_cell(self, cell) -> Optional[str]:
        spans = cell.find_all("span")
        if spans is None or len(spans) < 1:
            return None
        text = spans[1].get_text(strip=True) if hasattr(spans[1], "get_text") else str(spans[1])
        nums = re.findall(r"\d+", text)
        if len(nums) >= 1:
            return ''.join(nums)
        return None

    def get_game_score(self, game_page) -> Optional[dict]:
        scores_div = game_page.find_all("div", class_="stats-wrapper clearfix")
        if scores_div is None or len(scores_div) == 0:
            return None
        scores_tables = scores_div[0].find_all("table") if scores_div else None
        if scores_tables is None or len(scores_tables) == 0:
            return None

        rows = scores_tables[0].find_all("tr")
        if rows is None or len(rows) < 2:
            return None
        scores_row = rows[1]
        scores_tds = scores_row.find_all("td")
        away_score = self.__get_score_from_td_cell(scores_tds[0])
        home_score = self.__get_score_from_td_cell(scores_tds[1])
        return {"away": away_score,
                "home": home_score
                }

    def get_game_stats(self, game_page) -> Optional[dict]:
        teams_tables = game_page.find_all("table", class_="all-center")
        if teams_tables is None or len(teams_tables) == 0:
            return None

        home_stats = {}
        away_stats = {}
        rows = teams_tables[0].find_all("tr")
        team_name_row = rows[0]
        team_names = team_name_row.find_all("th")
        self.away_team = Utils.normalize_name(team_names[0].get_text(strip=True))
        self.home_team = Utils.normalize_name(team_names[2].get_text(strip=True))

        for row in rows:
            self.__process_row(row, away_stats, home_stats)

        return_object = {}
        return_object["away_team"] = Utils.normalize_name(self.away_team)
        return_object["home_team"] = Utils.normalize_name(self.home_team)
        return_object["away_stats"] = away_stats
        return_object["home_stats"] = home_stats
        return return_object

