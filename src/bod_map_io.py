"""Save and load custom Battle of Dots maps."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import orjson

from src.bod_constants import (
    AREA_PER_CITIES,
    CELL_SIZE,
    CITIES_PER_PLAYER,
    CITY_COLOR,
    RATIO,
    Coordinate,
    FOREST,
    HILL,
    MOUNTAIN,
    PLAINS,
    WATER,
)

MAP_VERSION = 1
MAPS_DIR = Path(__file__).resolve().parent.parent / "maps"

TERRAIN_PAINT = {
    "water": 0.05,
    "plains": 0.4,
    "hill": 0.75,
    "mountain": 0.92,
}

FOREST_PAINT = 0.65
FOREST_CLEAR = 0.2


def ensure_maps_dir() -> Path:
    MAPS_DIR.mkdir(parents=True, exist_ok=True)
    return MAPS_DIR


def world_size_for_players(players: int) -> tuple[int, int, int, int]:
    """Returns rows, cols, world_x, world_y for a player count."""
    area = players * CITIES_PER_PLAYER * AREA_PER_CITIES
    width = math.sqrt(area / RATIO)
    height = width * RATIO
    rows = int(int(width) // CELL_SIZE)
    cols = int(int(height) // CELL_SIZE)
    world_x = rows * CELL_SIZE
    world_y = cols * CELL_SIZE
    return rows, cols, world_x, world_y


def new_map_data(players: int) -> dict:
    rows, cols, world_x, world_y = world_size_for_players(players)
    return {
        "version": MAP_VERSION,
        "name": "untitled",
        "players": players,
        "rows": rows,
        "cols": cols,
        "world_x": world_x,
        "world_y": world_y,
        "cell_size": CELL_SIZE,
        "terrain": np.zeros((rows + 1, cols + 1), dtype=np.float32),
        "forest": np.full((rows + 1, cols + 1), FOREST_CLEAR, dtype=np.float32),
        "cities": {i: [] for i in range(players)}, # Dictionary by player
        "units": {i: [] for i in range(players)},  # Dictionary by player
    }

def map_data_to_save_payload(data: dict) -> dict:
    return {
        # ... rest of the fields ...
        "cities": {str(k): v for k, v in data["cities"].items()},
        "units": {str(k): v for k, v in data["units"].items()},
    }


def save_map(data: dict, path: Path | str) -> Path:
    path = Path(path)
    if path.suffix != ".json":
        path = path.with_suffix(".json")
    ensure_maps_dir()
    if not path.is_absolute():
        path = MAPS_DIR / path.name
    payload = map_data_to_save_payload(data)
    path.write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2))
    return path


def load_map(path: Path | str) -> dict:
    path = Path(path)
    if not path.is_absolute() and not path.exists():
        candidate = MAPS_DIR / path.name
        if candidate.exists():
            path = candidate
        elif not path.suffix:
            candidate = MAPS_DIR / f"{path.name}.json"
            if candidate.exists():
                path = candidate
    raw = orjson.loads(path.read_bytes())
    if raw.get("version", 0) != MAP_VERSION:
        raise ValueError(f"Unsupported map version: {raw.get('version')}")
    terrain = np.asarray(raw["terrain"], dtype=np.float32)
    forest = np.asarray(raw["forest"], dtype=np.float32)
    cities = [tuple(c) for c in raw["cities"]]
    return {
        "version": raw["version"],
        "name": raw.get("name", path.stem),
        "players": raw["players"],
        "rows": raw["rows"],
        "cols": raw["cols"],
        "world_x": raw["world_x"],
        "world_y": raw["world_y"],
        "cell_size": raw.get("cell_size", CELL_SIZE),
        "terrain": terrain,
        "forest": forest,
        "cities": cities,
        "path": str(path),
    }


def list_maps() -> list[Path]:
    ensure_maps_dir()
    return sorted(MAPS_DIR.glob("*.json"))


def choose_map_interactive() -> dict | None:
    maps = list_maps()
    if not maps:
        print("No saved maps found in", MAPS_DIR)
        return None
    print("\nSaved maps:")
    for i, p in enumerate(maps):
        print(f"  {i + 1}. {p.stem}")
    print("  0. Cancel")
    try:
        choice = int(input("Select map: "))
    except ValueError:
        return None
    if choice < 1 or choice > len(maps):
        return None
    return load_map(maps[choice - 1])


def validate_map_for_play(data: dict) -> list[str]:
    errors = []
    needed = data["players"] * CITIES_PER_PLAYER
    if len(data["cities"]) < needed:
        errors.append(
            f"Map has {len(data['cities'])} cities but needs at least {needed} "
            f"for {data['players']} players."
        )
    return errors
