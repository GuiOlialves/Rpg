"""Compatibility CLI: the current focused sprite and animation review."""
import argparse
from pathlib import Path
from review_character_overhaul import run, OUT

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUT)
    run(parser.parse_args().output)
