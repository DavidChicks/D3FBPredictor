"""Fetch https://www.d3football.com/teams/index and prepare it for parsing.

Usage:
  python get_teams.py         # fetch and save to data/teams_index.html (uses cache)
  python get_teams.py --force # re-fetch and overwrite
"""
from __future__ import annotations

import argparse
from dataclasses import field
import os
import logging
# from re import I
import re
from typing import Optional

import requests
from bs4 import BeautifulSoup
import json

import pprint

URL_ROOT = "https://www.d3football.com/"
URL = "https://www.d3football.com/teams/index"
DEFAULT_SAVE_PATH = os.path.join("data", "teams_index.html")


def fetch_url(url: str, timeout: int = 15) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; d3-teams-scraper/1.0)"
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def save_html(html: str, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def load_html(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def get_page(url: str = DEFAULT_SAVE_PATH, force: bool = False) -> BeautifulSoup:
    """Return a BeautifulSoup for the teams index page.

    If a saved copy exists and force is False, the saved copy will be used.
    Otherwise the page is fetched and saved to `save_path`.
    """
    # if not force and os.path.exists(save_path):
    #     logging.info("Loading cached page from %s", save_path)
    #     html = load_html(save_path)
    # else:
    logging.info("Fetching %s", url)
    html = fetch_url(url)
    # save_html(html, save_path)
    # logging.info("Saved page to %s", save_path)

    # Create parsing-ready BeautifulSoup object
    soup = BeautifulSoup(html, "html.parser")
    return soup


def get_all_teams_page(url: str = DEFAULT_SAVE_PATH, force: bool = False) -> BeautifulSoup:
    soup = get_page(url, force=force)
    teams_info = soup.find_all("div", class_="teaminfo")  # sanity check for expected content
    print(f"Found {len(teams_info)} teaminfo divs in the page.")
    teams_table = teams_info[0]
    teams = {}

    rows = teams_table.find_all("tr")
    for row in rows:
        # get the first anchor in the row
        anchor = row.find("a")
        if not anchor:
            continue
        link = anchor.get("href", "").strip()
        text = anchor.get_text(strip=True)
        # teams.append({"text": text, "link": link})
        teams[text] = link
        print(f"Found anchor: text={text!r}, link={link!r}")

    # save teams dict to a JSON file next to the saved HTML
    teams_out_dir = os.path.dirname(save_path) or "data"
    teams_out_path = os.path.join(teams_out_dir, "teams.json")
    try:
        os.makedirs(os.path.dirname(teams_out_path), exist_ok=True)
        with open(teams_out_path, "w", encoding="utf-8") as f:
            json.dump(teams, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(teams)} teams to {teams_out_path}")
    except Exception as e:
        print(f"Failed to save teams to {teams_out_path}: {e}")

    return teams


def get_team_page(team_url: str, year: int = None) -> Optional[BeautifulSoup]:
    print(f"Getting team page for {team_url} (year={year})")
    year_str = str(year) + "/" if year is not None else ""
    url = URL_ROOT + "teams/"
    url += team_url +"/"
    url += year_str
    print(f"  looking for team page at {url}")
    return get_page(url)


def get_team_games(team_url: str, year: int) -> list[dict]:
    print(f"Getting games for team {team_url} in year {year}")
    soup = get_team_page(team_url, year)
    # print(f"  get_team_page: {soup}")
    if (soup is None):
        print("  Failed to get team page.")
        return None
    # print(f"    Soup: {soup}")
    print("getting schedule table")
    teams_schedule = soup.find_all("table", class_="schedule") 
    if (teams_schedule is None or teams_schedule[0] is None):
        print("  Failed to find schedule table on team page.")
        return None
    print(f"  teams_schedule: teams_schedule")
    rows = teams_schedule[0].find_all("tr")
    print(f"  Processing rows: {str(len(rows))}")
    d3games = []
    for row in rows:
        opponent_link = None
        game_link = None
        opponent_name = None
        opponent_link = None
        print(f"  Processing row")
        # search row for the bullet marker "•"
        row_text = row.get_text()
        
        if "•" in row_text:
            print(f"    Found marker '•' in row text")
            anchors = row.find_all("a")
            for a in anchors:
                if a.get_text(strip=True) == "BX":
                    # print("    Found game link")
                    game_link=a.get("href", "").strip()
                else:
                    if opponent_link is None:
                        opponent_link = a.get("href", "").strip()
                    if opponent_name is None:
                        opponent_name = a.get_text(strip=True)
                    # print(f"    link text: {opponent_name}")
                    # print(f"    link target: {opponent_link}")
            new_game = {
                "game_link": game_link,
                "opponent_link": opponent_link,
                "opponent_name": opponent_name,
            }
            d3games.append(new_game)
            print(f"    Found {len(anchors)} anchors in row: {[a.get_text(strip=True) for a in anchors]}")
        else:
            print(f"    No marker '•' found in row text ({row.get_text(strip=True)})-- not a D3 opponent")
    return d3games


def get_game_page(game_url: str) -> Optional[BeautifulSoup]:
    print(f"Getting game page for {game_url}")
    url = URL_ROOT + game_url
    print(f"  looking for game page at {url}")
    return get_page(url)


def get_sub_fields(cell, sub_field_splitter: str, ignore_fields: str, expected_parts_count: int) -> list[str]:
    fields = []
    for sub_cell in cell.children:
        if ignore_fields is not None and str(sub_cell) == ignore_fields:
            # print(f"    Ignoring sub-cell: {sub_cell}")
            continue
        if sub_field_splitter is not None and sub_field_splitter in sub_cell.get_text():
            parts = sub_cell.get_text(strip=True).split(sub_field_splitter)
            pprint.pp(f"    Splitting sub-cell into parts: {parts}")
            fields.extend(parts)
        else:
            fields.append(sub_cell.get_text(strip=True))
    if len(fields) != expected_parts_count:
        print(f"     Incorrect split count in cell for stat {cell} (expected {expected_parts_count} but got {len(fields)})")
        return None
    return fields


def get_percentage_parts(cell) -> list[str]:
    text = cell.get_text(strip=True) if hasattr(cell, "get_text") else str(cell)
    nums = re.findall(r"\d+", text)
    if len(nums) >= 2:
        return [
            nums[-2],
            nums[-1],
            str(int(nums[-2])/int(nums[-1])) if (nums[-1] != "0") else "0"
        ]
    return []


def get_game_stats(game_url: str) -> Optional[dict]:
    game_page = get_game_page(game_url)
    if game_page is None:
        print("  Failed to get game page.")
        print("  Failed to get game page.")
        return None
    teams_table = game_page.find_all("table", class_="all-center")
    if teams_table is None or len(teams_table) == 0:
        print("  Failed to find teams info table on game page.")
        return None
    home_stats = {}
    away_stats = {}
    rows = teams_table[0].find_all("tr")
    team_name_row = rows[0]
    team_names = team_name_row.find_all("th")
    team_away = team_names[0].get_text(strip=True)
    team_home = team_names[2].get_text(strip=True)

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
            stat_splitter_key_postremove: "EFFICIENCY",
            stat_splitter_key_success: "Conversions",
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

    }
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
        if stat in stat_splitter:
            print(f"  Found stat with special splitting rules: {stat}")
            stat_spliting = stat_splitter[stat]
            field_names = []
            away_sub_stats = []
            home_sub_stats = []
            if stat_spliting[stat_splitter_type] == stat_splitter_type_percent:
                cell_type = type(cells[0])
                name = cells[1].get_text(strip=True)
                if stat_splitter_key_postremove in stat_spliting:
                    name = name.replace(stat_spliting[stat_splitter_key_postremove], "")
                name = name.strip()
                values_away = get_percentage_parts(cells[0])
                values_home = get_percentage_parts(cells[2])
                away_stats[name + stat_spliting[stat_splitter_key_success]] = values_away[0]
                home_stats[name + stat_spliting[stat_splitter_key_success]] = values_home[0]
                away_stats[name + " Total"] = values_away[1]
                home_stats[name + " Total"] = values_home[1]
                away_stats[name + stat_spliting[stat_splitter_key_postremove]] = values_away[2]
                home_stats[name + stat_spliting[stat_splitter_key_postremove]] = values_home[2]

            else:
                expectted_fields_count = stat_spliting[stat_spliiter_expectted_fields_count]
                field_names = get_sub_fields(cells[1], 
                                             stat_spliting[stat_splitter_field_splitter],
                                             stat_spliting[stat_splitter_ignore_fields],
                                             expectted_fields_count)
                if stat_spliting[stat_splitter_key_prepend] is not None:
                    field_names = [stat_spliting[stat_splitter_key_prepend] + name for name in field_names]
                away_sub_stats = get_sub_fields(cells[0],
                                                stat_spliting[stat_splitter_field_splitter],
                                                stat_spliting[stat_splitter_ignore_fields],
                                                expectted_fields_count)
                home_sub_stats = get_sub_fields(cells[2],
                                                stat_spliting[stat_splitter_field_splitter],
                                                stat_spliting[stat_splitter_ignore_fields],
                                                expectted_fields_count)

            pprint.pp(f"    field_names: {field_names}")

            if field_names is None or away_sub_stats is None or home_sub_stats is None:
                print(f"     Incorrect split count in row for stat {stat} (fields={len(field_names)}, away_stats={len(away_stats)}, home_stats={len(home_stats)}), skipping")
                continue
            if stat_spliting[stat_splitter_field_splitter_field_header_determiner] is not None:
                determiner = stat_spliting[stat_splitter_field_splitter_field_header_determiner]
                field_header = None
                print(f"         Looking for field header '{determiner}' in field names:")
                for field_name in field_names:
                    print(f"           Looking at {field_name}")
                    if determiner in field_name:
                        parts = field_name.split(determiner)
                        field_header = parts[0]
                        print(f"           Found field header '{field_header}' in field names")
                        break
                if field_header is not None:
                    # for field_name in field_names:
                    #     if not field_name.startswith(field_header):
                    #         field_name = field_header + determiner + field_name
                    #         print(f"     new field name '{field_name}")
                    field_names = [
                         (field_header + determiner + field_name if not field_name.startswith(field_header) else field_name)
                         for field_name in field_names
                         ]

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


def undate_field_names(field_names: list[str], stat_splitting) -> list[str]:
    if stat_splitting[stat_splitter_field_splitter_field_header_determiner] is not None:
        determiner = stat_splitting[stat_splitter_field_splitter_field_header_determiner]
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


def get_and_save_game_stats(game_url: str, out_path: str) -> None:
    stats = get_game_stats(game_url)
    end = game_url.split("/")[-1]
    parts = end.split(".")[0].split("_")
    # ensure parts[0] is 8 characters long and all digits (YYYYMMDD)
    if not parts:
        print(f"Unexpected file name format; no parts found in '{without_extension}'")
        return stats

    if not (len(parts[0]) == 8 and parts[0].isdigit()):
        print(f"Unexpected file name format; expected parts[0] to be 8 digits but got: {parts[0]!r}")

    year_prefix = parts[0][:4]
    date = parts[0][4:]
    
    file_path = os.path.join(out_path, f"{year_prefix}", f"{year_prefix}_{date}_{parts[1]}.json")

    # save the stats object as JSON to file_path
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        print(f"Saved stats to {file_path}")
    except Exception as e:
        print(f"Failed to save stats to {file_path}: {e}")

    return stats


def main() -> None:

    parser = argparse.ArgumentParser()
    parser.add_argument("--force", "-f", action="store_true", help="re-fetch even if cached")
    parser.add_argument("--out", "-o", default=DEFAULT_SAVE_PATH, help="output file path")
    args = parser.parse_args()

    # logging.basicConfig(level=logging.INFO, "https://www.d3football.com/teams/index", force=args.force)
    # get_all_teams_page("https://www.d3football.com/teams/index")

    # games = get_team_games("linfield", 2021)
    # print(f"Found games for Linfield in 2021")
    # pprint.pp(games)
    game_stats = get_and_save_game_stats("/seasons/2025/boxscores/20251004_xmdh.xml", os.path.join("data", "games"))
    pprint.pp(game_stats)


if __name__ == "__main__":
    main()
