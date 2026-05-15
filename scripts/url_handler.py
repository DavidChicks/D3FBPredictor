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
from re import M
import requests
import time
from bs4 import BeautifulSoup

from iurl_handler import IUrl_Handler

class Url_Handler(IUrl_Handler):
    URL_ROOT = "https://www.d3football.com/"
    URL = "https://www.d3football.com/teams/index"
    DEFAULT_SAVE_PATH = os.path.join("data", "teams_index.html")

    def __fetch_url(self, url: str, timeout: int = 15) -> str:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; d3-teams-scraper/1.0)"
        }
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.text


    def __get_page(self, url: str, max_retries: int = 0) -> BeautifulSoup:
        """Return a BeautifulSoup for the teams index page.

        If a saved copy exists and force is False, the saved copy will be used.
        Otherwise the page is fetched and saved to `save_path`.
        """
        logging.info("Fetching %s", url)
        retries = 0
        while True:
            try:
                html = self.__fetch_url(url)
                # Create parsing-ready BeautifulSoup object
                soup = BeautifulSoup(html, "html.parser")
                return soup
            except requests.RequestException as e:
                if retries < max_retries:
                    logging.warning("Error fetching %s: %s. Retrying...", url, e)
                    retries += 1
                    logging.warning("  Waiting %d seconds before retrying...", 60 * retries)
                    time.sleep(60 * retries)
                    continue
                logging.error("Failed to fetch %s: %s. No more retries.", url, e)
                raise e


    def get_team_page(self, team: str, year: str, max_retries: int = 0) -> BeautifulSoup:
        full_url = Url_Handler.URL_ROOT + "teams/" + team + "/" + year + "/index"
        return self.__get_page(full_url, max_retries)


    def get_game_page(self, game_url: str, max_retries = 0) -> BeautifulSoup:
        ## https://www.d3football.com/seasons/2025/boxscores/20251115_82vt.xml
        url = Url_Handler.URL_ROOT + game_url
        return self.__get_page(url, max_retries)
