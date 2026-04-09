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
import requests
from bs4 import BeautifulSoup



class Url_Utils:
    URL_ROOT = "https://www.d3football.com/"
    URL = "https://www.d3football.com/teams/index"
    DEFAULT_SAVE_PATH = os.path.join("data", "teams_index.html")

    @staticmethod
    def fetch_url(url: str, timeout: int = 15) -> str:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; d3-teams-scraper/1.0)"
        }
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.text


    @staticmethod
    def save_html(html: str, path: str) -> None:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)

    @staticmethod
    def load_html(path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()


    @staticmethod
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
        html = Url_Utils.fetch_url(url)
        # save_html(html, save_path)
        # logging.info("Saved page to %s", save_path)

        # Create parsing-ready BeautifulSoup object
        soup = BeautifulSoup(html, "html.parser")
        return soup

