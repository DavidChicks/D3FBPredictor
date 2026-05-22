"""Utility helpers."""
from __future__ import annotations

from calendar import SATURDAY, WEDNESDAY
import datetime
import logging
import time


class Utils:
    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize a team name to a filesystem/key friendly form.

        Examples:
            "Linfield" -> "linfield"
            "Lewis & Clark" -> "lewis_and_clark"
        """
        normalized = name.strip().lower()
        normalized = normalized.replace("&", "and").replace(" ", "_").replace("-", "_").replace(".", "").replace("'", "").replace("(", "").replace(")", "")
        return normalized


    @staticmethod
    def add_element_to_list_at_index(lst: list, index: int, element):
        while len(lst) <= index:
            lst.append(None)
        lst[index] = element


    @staticmethod
    def get_week_from_file_name(file_name: str) -> int:
        # extract the week from a file name like "20240907_linfield_wooster.json"
        # earliest possible game is Sept 1st, so assume the week from 1-7 is first week, etc.
        parts = file_name.split(".")[0].split("_")
        if len(parts) < 2:
            logging.error(f"Unexpected file name format; expected at least 3 parts but got: {parts}")
            return None
        date_part = parts[0]
        if len(date_part) != 8 or not date_part.isdigit():
            logging.error(f"Unexpected date format in file name; expected 8 digits but got: {date_part}")
            return None
        month_day = date_part[4:]
        year = int(date_part[:4])
        month = int(month_day[:2])
        day = int(month_day[2:])

        if (year is None or month is None or day is None):
            logging.error(f"Failed to extract date from file name: {file_name}: year={year}, month={month}, day={day}")
            return None

        game_day = datetime.date(year, month, day)
        sept_first = datetime.date(year, 9, 1)
        delta = abs((game_day - sept_first).days)
        day_of_week = game_day.weekday() # 0 = Monday; 6 = Sunday
        if not day_of_week == SATURDAY: 
            if day_of_week >= WEDNESDAY:
                shift = SATURDAY - day_of_week
            else:
                shift = -(day_of_week + 2)
            delta += shift
        if delta < 0:
            logging.info("Game day too early in year")
            if year > 2025 and month == 1:
                logging.info("National Championship game")
                return 16
            else:
                logging.error("Invalid game date, irngoring")
                return None

        return int(delta / 7)
