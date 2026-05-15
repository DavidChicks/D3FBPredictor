"""Utility helpers."""
#from __future__ import annotations

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
        #print(f"  Adding element at index {index}: {element}")
        while len(lst) <= index:
            lst.append(None)
        lst[index] = element
