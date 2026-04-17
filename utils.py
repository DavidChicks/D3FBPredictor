"""Utility helpers."""
from __future__ import annotations

class Utils:
    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize a team name to a filesystem/key friendly form.

        Examples:
            "Linfield" -> "linfield"
            "Wheaton (IL)" -> "wheaton_il"
        """
        normalized = name.strip().lower()
        normalized = normalized.replace("&", "and").replace(" ", "_").replace("-", "_").replace(".", "")
        return normalized
