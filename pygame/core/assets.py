"""Asset loading relative to the Pygame project directory."""
from pathlib import Path

import pygame

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> pygame.Surface:
    return pygame.image.load(ROOT / path).convert_alpha()
