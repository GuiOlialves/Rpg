"""Civilian looks from the original O Vale pixel-art pack."""
from ui.character_art import character_sheet


def civilian_sheet(load, look):
    character = {"resident": "man", "shopkeeper": "woman",
                 "merchant": "merchant", "elder": "elder", "worker": "worker"}[look]
    # Column zero is neutral. The other columns remain available to moving NPCs.
    return character_sheet(load, f"civilian_{character}", "walk")
