"""Pygame map editor for Battle of Dots."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pygame

from src.bod_client import marching_squares_layers, marching_squares_poly
from src.bod_constants import (
    CELL_SIZE,
    CITIES_PER_PLAYER,
    CITY_COLOR,
    CITY_R,
    FOREST,
    HILL,
    MOUNTAIN,
    PLAINS,
    TERRAIN_TYPES,
    WATER,
)
from src.bod_map_io import (
    FOREST_CLEAR,
    FOREST_PAINT,
    TERRAIN_PAINT,
    ensure_maps_dir,
    list_maps,
    load_map,
    new_map_data,
    save_map,
)

TOOLS = ["water", "plains", "hill", "mountain", "forest", "erase_forest", "city", "unit"]
PLAYER_COLORS = [(255, 50, 50), (50, 255, 50), (50, 50, 255), (255, 255, 50), (255, 50, 255), (50, 255, 255)]

class MapBrush:
    def __init__(self, radius: float = 50.0, strength: float = 1.0) -> None:
        self.radius = radius
        self.strength = strength

    def apply(self, grid: np.ndarray, mx: float, my: float, target: float) -> None:
        cs = CELL_SIZE
        r = self.radius
        rows, cols = grid.shape[0] - 1, grid.shape[1] - 1

        col_start = max(0, int((my - r) / cs))
        col_end = min(cols + 1, int((my + r) / cs) + 1)
        row_start = max(0, int((mx - r) / cs))
        row_end = min(rows + 1, int((mx + r) / cs) + 1)

        inv_r = 1.0 / r
        strength = self.strength

        for j in range(row_start, row_end):
            px = j * cs
            dx_sq = (px - mx) ** 2
            for i in range(col_start, col_end):
                py = i * cs
                dist_sq = (py - my) ** 2 + dx_sq
                if dist_sq <= r * r:
                    dist = math.sqrt(dist_sq)
                    weight = strength * (1.0 - dist * inv_r * 0.5)
                    old = grid[j, i]
                    grid[j, i] = max(0.0, min(1.0, old + (target - old) * weight))


class MapEditor:
    def __init__(self, data: dict) -> None:
        self.data = data
        self.rows = data["rows"]
        self.cols = data["cols"]
        self.world_x = data["world_x"]
        self.world_y = data["world_y"]
        self.terrain = np.asarray(data["terrain"], dtype=np.float32)
        self.forest = np.asarray(data["forest"], dtype=np.float32)
        self.cities = data.get("cities", {i: [] for i in range(data["players"])})
        self.units = data.get("units", {i: [] for i in range(data["players"])})

        pygame.init()
        info = pygame.display.Info()
        self.screen_size = (info.current_w - 20, info.current_h - 100)
        self.factor = min(
            self.screen_size[0] / self.world_x,
            self.screen_size[1] / self.world_y,
        )
        self.screen = pygame.display.set_mode(self.screen_size)
        pygame.display.set_caption(f"Map Editor — {data.get('name', 'untitled')}")
        pygame.event.set_allowed(
            [
                pygame.KEYDOWN,
                pygame.QUIT,
                pygame.MOUSEBUTTONDOWN,
                pygame.MOUSEBUTTONUP,
                pygame.MOUSEMOTION,
                pygame.MOUSEWHEEL,
            ]
        )
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 22)
        self.small_font = pygame.font.SysFont(None, 18)
        self.done = False
        self.dirty = True

        self.zoom_levels = [0.5, 0.75, 1, 1.2, 1.5, 2, 2.5, 3, 4]
        self.zoom_idx = self.zoom_levels.index(1)
        self.zoom = self._zoom_at(self.zoom_idx)
        self.camx, self.camy = 0.0, 0.0
        self.panning = False
        self.painting = False
        self.pan_start_mouse = (0, 0)
        self.pan_start_cam = (0.0, 0.0)

        self.tool_idx = 1
        self.brush = MapBrush(55.0, 1.0)
        self.city_brush = MapBrush(8.0, 1.0)
        self.terrain_by_zoom: dict[float, pygame.Surface] = {}
        self.selected_player = 0


    def _zoom_at(self, idx: int) -> float:
        return self.zoom_levels[idx] * self.factor

    def run(self) -> None:
        self._rebuild_terrain_cache()
        while not self.done:
            self._handle_events()
            self._draw()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()

    def _sync_data(self) -> None:
        self.data.update({"terrain": self.terrain, "forest": self.forest, "cities": self.cities, "units": self.units})

    def _world_from_screen(self, sx: int, sy: int) -> tuple[float, float]:
        return self.camx + sx / self.zoom, self.camy + sy / self.zoom

    def _apply_tool_at(self, wx: float, wy: float) -> None:
        tool = TOOLS[self.tool_idx]
        if tool == "city":
            self._toggle_entity(self.cities[self.selected_player], wx, wy)
        elif tool == "unit":
            self._toggle_entity(self.units[self.selected_player], wx, wy)
        else:
            self.dirty = True


    def _toggle_entity(self, collection: list, wx: float, wy: float) -> None:
        # Toggle: delete if near, otherwise add
        for i, (ex, ey) in enumerate(collection):
            if math.hypot(wx - ex, wy - ey) < 15: # Tolerance in world units
                collection.pop(i)
                return
        collection.append((wx, wy))


    def _handle_events(self) -> None:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.done = True
            elif e.type == pygame.KEYDOWN:
                self._handle_key(e)
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 3:
                    self.panning = True
                    self.pan_start_mouse = e.pos
                    self.pan_start_cam = (self.camx, self.camy)
                elif e.button == 1:
                    self.painting = True
                    wx, wy = self._world_from_screen(*e.pos)
                    self._apply_tool_at(wx, wy)
            elif e.type == pygame.MOUSEBUTTONUP:
                if e.button == 3:
                    self.panning = False
                elif e.button == 1:
                    self.painting = False
            elif e.type == pygame.MOUSEMOTION:
                if self.painting:
                    wx, wy = self._world_from_screen(*e.pos)
                    self._apply_tool_at(wx, wy)
                elif self.panning:
                    mx, my = e.pos
                    sx, sy = self.pan_start_mouse
                    self.camx = self.pan_start_cam[0] - (mx - sx) / self.zoom
                    self.camy = self.pan_start_cam[1] - (my - sy) / self.zoom
                    self._clamp_camera()
            elif e.type == pygame.MOUSEWHEEL and e.y != 0:
                mx, my = pygame.mouse.get_pos()
                if e.y > 0 and self.zoom_idx < len(self.zoom_levels) - 1:
                    self._set_zoom(self.zoom_idx + 1, (mx, my))
                elif e.y < 0 and self.zoom_idx > 0:
                    self._set_zoom(self.zoom_idx - 1, (mx, my))

    def _handle_key(self, e: pygame.event.Event) -> None:
        if e.key == pygame.K_ESCAPE:
            self.done = True
        elif pygame.K_1 <= e.key <= pygame.K_8:
            self.tool_idx = e.key - pygame.K_1
        elif e.key == pygame.K_s:
            self._save_dialog()
        elif e.key == pygame.K_g:
            self._generate_island()
        elif e.key == pygame.K_LEFTBRACKET:
            self.brush.radius = max(10, self.brush.radius - 10)
        elif e.key == pygame.K_RIGHTBRACKET:
            self.brush.radius = min(200, self.brush.radius + 10)
        elif e.key == pygame.K_p:
            self.selected_player = (self.selected_player + 1) % self.data["players"]

    def _save_dialog(self) -> None:
        self._sync_data()
        name = input("\nMap filename (without .json): ").strip() or self.data.get(
            "name", "untitled"
        )
        self.data["name"] = name
        path = save_map(self.data, name)
        print(f"Saved to {path}")

    def _generate_island(self) -> None:
        """Quick-fill a playable island using the same logic as the server."""
        import random

        import perlin_noise

        from src.bod_constants import CITY_DISTANCE, CITY_PLACE_TRIES, PLAINS, THRESHOLD

        players = self.data["players"]
        noise = perlin_noise.PerlinNoise(octaves=3)

        def coastal_bias(x: float, y: float) -> float:
            cx, cy = self.rows / 2, self.cols / 2
            dx, dy = abs(x - cx), abs(y - cy)
            dist = math.sqrt(dx**2 + dy**2)
            max_dist = math.sqrt(cx**2 + cy**2)
            nd = dist / max_dist
            if nd <= 0.5:
                return 0.5 + max(nd, 0.25)
            return 1 - ((nd - 0.5) * 2)

        for y in range(self.cols + 1):
            for x in range(self.rows + 1):
                self.terrain[x, y] = max(
                    0,
                    min(
                        1,
                        ((noise([x / 25, y / 25])) - 0.2)
                        + ((coastal_bias(x, y) * 1.2) - 0.2),
                    ),
                )

        forest_noise = perlin_noise.PerlinNoise(octaves=1.1)
        for y in range(self.cols + 1):
            for x in range(self.rows + 1):
                tv = self.terrain[x, y]
                value = (min(0.6, forest_noise([x / 30, y / 30])) * 2.0) + 0.3
                plains_diff = max(0, (PLAINS.threshold + 0.1) - tv)
                hill_diff = max(0, tv - (HILL.threshold - 0.1))
                self.forest[x, y] = value - plains_diff * 10 - hill_diff * 10

        self.cities = {i: [] for i in range(players)}
        tries = 0
        distance = CITY_DISTANCE
        total_cities = 0
        while total_cities < players * CITIES_PER_PLAYER:
            cx = random.randint(0, self.rows)
            cy = random.randint(0, self.cols)
            tv = self.terrain[cx, cy]
            if (
                PLAINS.threshold < tv < HILL.threshold
                and all(
                    abs(cx * CELL_SIZE - c[0]) + abs(cy * CELL_SIZE - c[1])
                    >= CELL_SIZE * distance
                    for player_cities in self.cities.values()
                    for c in player_cities
                )
                and 1 <= cx <= self.rows - 1
                and 1 <= cy <= self.cols - 1
                and self.forest[cx, cy] < THRESHOLD
            ):
                player_id = total_cities % players
                self.cities[player_id].append((cx * CELL_SIZE, cy * CELL_SIZE))
                total_cities += 1
                distance = CITY_DISTANCE
            tries += 1
            if tries >= CITY_PLACE_TRIES:
                distance = max(1, distance - 1)
                tries = 0
        self.dirty = True
        self._rebuild_terrain_cache()

    def _set_zoom(self, new_idx: int, screen_pos: tuple[int, int]) -> None:
        old_z = self.zoom
        new_z = self._zoom_at(new_idx)
        sx, sy = screen_pos
        wx = self.camx + sx / old_z
        wy = self.camy + sy / old_z
        self.zoom_idx = new_idx
        self.zoom = new_z
        self.camx = wx - sx / new_z
        self.camy = wy - sy / new_z
        self._clamp_camera()

    def _clamp_camera(self) -> None:
        max_x = max(0.0, self.world_x - self.screen_size[0] / self.zoom)
        max_y = max(0.0, self.world_y - self.screen_size[1] / self.zoom)
        self.camx = max(0.0, min(self.camx, max_x))
        self.camy = max(0.0, min(self.camy, max_y))

    def _rebuild_terrain_cache(self) -> None:
        thresholds = [t.threshold for t in TERRAIN_TYPES if t is not FOREST]
        layers = marching_squares_layers(
            self.terrain, CELL_SIZE, self.rows, self.cols, thresholds
        )
        layers.append(
            marching_squares_poly(
                self.forest, CELL_SIZE, self.rows, self.cols, FOREST.threshold
            )
        )
        colors = [WATER.color, PLAINS.color, HILL.color, MOUNTAIN.color, FOREST.color]
        self.terrain_by_zoom = {}
        for zl in self.zoom_levels:
            z = zl * self.factor
            sw = max(1, int(self.world_x * z))
            sh = max(1, int(self.world_y * z))
            surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            for layer, color in zip(layers, colors):
                for poly in layer:
                    scaled = [(int(x * z), int(y * z)) for x, y in poly]
                    pygame.draw.polygon(surf, color, scaled, 0)
            for p_id in range(self.data["players"]):
                color = PLAYER_COLORS[p_id]
                for (cx, cy) in self.cities[p_id]:
                    pygame.draw.circle(surf, color, (int(cx*z), int(cy*z)), int(CITY_R*z))
                for (ux, uy) in self.units[p_id]:
                    # Draw square for units
                    rect = (int((ux-5)*z), int((uy-5)*z), int(10*z), int(10*z))
                    pygame.draw.rect(surf, color, rect)
            self.terrain_by_zoom[z] = surf
        self.dirty = False

    def _draw(self) -> None:
        if self.dirty:
            self._rebuild_terrain_cache()
        self.screen.fill((40, 40, 50))
        z = self.zoom
        ox, oy = int(-self.camx * z), int(-self.camy * z)
        self.screen.blit(self.terrain_by_zoom[z], (ox, oy))

        tool = TOOLS[self.tool_idx]
        total_cities = sum(len(cities) for cities in self.cities.values())
        lines = [
             f"Editing Player {self.selected_player + 1} (Color: {PLAYER_COLORS[self.selected_player]})",
                "Press 'P' to switch player | 1-8: tools",
            f"Map: {self.data.get('name', 'untitled')} | Players: {self.data['players']}",
            f"Tool [{self.tool_idx + 1}]: {tool} | Brush radius: {int(self.brush.radius)}",
            f"Cities: {total_cities} / {self.data['players'] * CITIES_PER_PLAYER} needed",
            "1-8: tools | Drag LMB: paint | RMB: pan | Wheel: zoom",
            "[ ]: brush size | G: generate island | S: save | Esc: quit",
            "Tools: 1=water 2=plains 3=hill 4=mountain 5=forest 6=clear forest 7=city 8=unit",
        ]
        y = 8
        for line in lines:
            surf = self.font.render(line, True, (240, 240, 240))
            self.screen.blit(surf, (8, y))
            y += 22

    @staticmethod
    def _pick_map_file() -> dict | None:
        maps = list_maps()
        if not maps:
            print("No maps in", ensure_maps_dir())
            return None
        for i, p in enumerate(maps):
            print(f"  {i + 1}. {p.stem}")
        try:
            idx = int(input("Select map to edit: "))
        except ValueError:
            return None
        if idx < 1 or idx > len(maps):
            return None
        return load_map(maps[idx - 1])


def main() -> None:
    print("=== Battle of Dots Map Editor ===\n")
    print("1. New map")
    print("2. Load existing map")
    try:
        mode = input("> ").strip()
    except EOFError:
        return

    if mode == "2":
        data = MapEditor._pick_map_file()
        if data is None:
            return
    else:
        try:
            players = int(input("Players for this map (2-6): "))
            players = max(2, min(6, players))
        except ValueError:
            players = 2
        data = new_map_data(players)
        gen = input("Generate random island? (y/n): ").strip().lower()
        editor = MapEditor(data)
        if gen in ("y", "yes", ""):
            editor._generate_island()
        editor.run()
        return

    MapEditor(data).run()


if __name__ == "__main__":
    main()
