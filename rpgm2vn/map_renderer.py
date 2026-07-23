"""Render RPG Maker MV/MZ maps to PNGs for use as VN backgrounds."""

import os
from pathlib import Path
from PIL import Image


# Tile ID constants from rmmz_core.js
TILE_ID_B = 0
TILE_ID_C = 256
TILE_ID_D = 512
TILE_ID_E = 768
TILE_ID_A5 = 1536
TILE_ID_A1 = 2048
TILE_ID_A2 = 2816
TILE_ID_A3 = 4352
TILE_ID_A4 = 5888
TILE_ID_MAX = 8192


# Autotile shape tables from rmmz_core.js
FLOOR_AUTOTILE_TABLE = [
    [[2, 4], [1, 4], [2, 3], [1, 3]],
    [[2, 0], [1, 4], [2, 3], [1, 3]],
    [[2, 4], [3, 0], [2, 3], [1, 3]],
    [[2, 0], [3, 0], [2, 3], [1, 3]],
    [[2, 4], [1, 4], [2, 3], [3, 1]],
    [[2, 0], [1, 4], [2, 3], [3, 1]],
    [[2, 4], [3, 0], [2, 3], [3, 1]],
    [[2, 0], [3, 0], [2, 3], [3, 1]],
    [[2, 4], [1, 4], [2, 1], [1, 3]],
    [[2, 0], [1, 4], [2, 1], [1, 3]],
    [[2, 4], [3, 0], [2, 1], [1, 3]],
    [[2, 0], [3, 0], [2, 1], [1, 3]],
    [[2, 4], [1, 4], [2, 1], [3, 1]],
    [[2, 0], [1, 4], [2, 1], [3, 1]],
    [[2, 4], [3, 0], [2, 1], [3, 1]],
    [[2, 0], [3, 0], [2, 1], [3, 1]],
    [[0, 4], [1, 4], [0, 3], [1, 3]],
    [[0, 4], [3, 0], [0, 3], [1, 3]],
    [[0, 4], [1, 4], [0, 3], [3, 1]],
    [[0, 4], [3, 0], [0, 3], [3, 1]],
    [[2, 2], [1, 2], [2, 3], [1, 3]],
    [[2, 2], [1, 2], [2, 3], [3, 1]],
    [[2, 2], [1, 2], [2, 1], [1, 3]],
    [[2, 2], [1, 2], [2, 1], [3, 1]],
    [[2, 4], [3, 4], [2, 3], [3, 3]],
    [[2, 4], [3, 4], [2, 1], [3, 3]],
    [[2, 0], [3, 4], [2, 3], [3, 3]],
    [[2, 0], [3, 4], [2, 1], [3, 3]],
    [[2, 4], [1, 4], [2, 5], [1, 5]],
    [[2, 0], [1, 4], [2, 5], [1, 5]],
    [[2, 4], [3, 0], [2, 5], [1, 5]],
    [[2, 0], [3, 0], [2, 5], [1, 5]],
    [[0, 4], [3, 4], [0, 3], [3, 3]],
    [[2, 2], [1, 2], [2, 5], [1, 5]],
    [[0, 2], [1, 2], [0, 3], [1, 3]],
    [[0, 2], [1, 2], [0, 3], [3, 1]],
    [[2, 2], [3, 2], [2, 3], [3, 3]],
    [[2, 2], [3, 2], [2, 1], [3, 3]],
    [[2, 4], [3, 4], [2, 5], [3, 5]],
    [[2, 0], [3, 4], [2, 5], [3, 5]],
    [[0, 4], [1, 4], [0, 5], [1, 5]],
    [[0, 4], [3, 0], [0, 5], [1, 5]],
    [[0, 2], [3, 2], [0, 3], [3, 3]],
    [[0, 2], [1, 2], [0, 5], [1, 5]],
    [[0, 4], [3, 4], [0, 5], [3, 5]],
    [[2, 2], [3, 2], [2, 5], [3, 5]],
    [[0, 2], [3, 2], [0, 5], [3, 5]],
    [[0, 0], [1, 0], [0, 1], [1, 1]],
]

WALL_AUTOTILE_TABLE = [
    [[2, 2], [1, 2], [2, 1], [1, 1]],
    [[0, 2], [1, 2], [0, 1], [1, 1]],
    [[2, 0], [1, 0], [2, 1], [1, 1]],
    [[0, 0], [1, 0], [0, 1], [1, 1]],
    [[2, 2], [3, 2], [2, 1], [3, 1]],
    [[0, 2], [3, 2], [0, 1], [3, 1]],
    [[2, 0], [3, 0], [2, 1], [3, 1]],
    [[0, 0], [3, 0], [0, 1], [3, 1]],
    [[2, 2], [1, 2], [2, 3], [1, 3]],
    [[0, 2], [1, 2], [0, 3], [1, 3]],
    [[2, 0], [1, 0], [2, 3], [1, 3]],
    [[0, 0], [1, 0], [0, 3], [1, 3]],
    [[2, 2], [3, 2], [2, 3], [3, 3]],
    [[0, 2], [3, 2], [0, 3], [3, 3]],
    [[2, 0], [3, 0], [2, 3], [3, 3]],
    [[0, 0], [3, 0], [0, 3], [3, 3]],
]

WATERFALL_AUTOTILE_TABLE = [
    [[2, 0], [1, 0], [2, 1], [1, 1]],
    [[0, 0], [1, 0], [0, 1], [1, 1]],
    [[2, 0], [3, 0], [2, 1], [3, 1]],
    [[0, 0], [3, 0], [0, 1], [3, 1]],
]


class MapRenderer:
    """Best-effort map renderer using Pillow.

    Renders MV/MZ map layers 0-3 into a PNG. Autotiles are drawn using the
    same tables as RPG Maker, but animation uses the first frame only.
    """

    def __init__(self, data, tile_width=48, tile_height=48):
        self.data = data
        self.tile_width = tile_width
        self.tile_height = tile_height

    def render_all(self, game_dir, target_size=None):
        """Render all maps with a tileset and return the set of map ids rendered."""
        rendered = set()
        out_dir = Path(game_dir) / "images" / "map_bg"
        out_dir.mkdir(parents=True, exist_ok=True)
        for map_id in self.data.list_map_ids():
            try:
                path = self.render_map(map_id, out_dir, target_size=target_size)
                if path:
                    rendered.add(map_id)
            except Exception:
                # Best-effort: skip maps that fail to render.
                pass
        return rendered

    def render_map(self, map_id, out_dir, target_size=None):
        map_data = self.data.get_map(map_id)
        if not map_data:
            return None
        tileset_id = map_data.get("tilesetId", 1)
        tileset = self._get_tileset(tileset_id)
        if not tileset:
            return None
        tileset_names = tileset.get("tilesetNames", []) or []
        images = self._load_tileset_images(tileset_names)
        if all(img is None for img in images):
            return None

        width = map_data.get("width", 0)
        height = map_data.get("height", 0)
        data = map_data.get("data", [])
        if not width or not height or len(data) < width * height * 6:
            return None

        canvas = Image.new("RGBA", (width * self.tile_width, height * self.tile_height), (0, 0, 0, 0))
        # Draw layers 0-3 (bottom to top). Layers 4 and 5 are shadows/regions.
        for z in range(4):
            for y in range(height):
                for x in range(width):
                    tile_id = data[(z * height + y) * width + x]
                    if not _is_visible_tile(tile_id):
                        continue
                    dx = x * self.tile_width
                    dy = y * self.tile_height
                    if _is_autotile(tile_id):
                        self._draw_autotile(canvas, images, tile_id, dx, dy)
                    else:
                        self._draw_normal_tile(canvas, images, tile_id, dx, dy)

        # If the canvas is fully transparent, skip it.
        if canvas.getextrema()[3][1] == 0:
            return None

        if target_size:
            canvas = self._fit_canvas(canvas, target_size)

        out_path = Path(out_dir) / f"map_{map_id:03d}.png"
        canvas.save(out_path, "PNG")
        return out_path

    def _get_tileset(self, tileset_id):
        tilesets = self.data.tilesets
        if isinstance(tilesets, list) and 0 <= tileset_id < len(tilesets):
            return tilesets[tileset_id]
        if isinstance(tilesets, dict):
            return tilesets.get(str(tileset_id)) or tilesets.get(tileset_id)
        return None

    def _load_tileset_images(self, tileset_names):
        """Load tileset images in setNumber order: A1, A2, A3, A4, A5, B, C, D, E."""
        img_dir = Path(self.data.data_dir).parent / "img" / "tilesets"
        images = []
        for name in tileset_names:
            if not name:
                images.append(None)
                continue
            path = img_dir / f"{name}.png"
            if path.exists():
                images.append(Image.open(path).convert("RGBA"))
            else:
                images.append(None)
        return images

    def _draw_normal_tile(self, canvas, images, tile_id, dx, dy):
        if _is_tile_a5(tile_id):
            set_number = 4
            tile_index = tile_id - TILE_ID_A5
        else:
            set_number = 5 + tile_id // 256
            tile_index = tile_id
        img = images[set_number]
        if img is None:
            return
        w, h = self.tile_width, self.tile_height
        sx = ((tile_index // 128) % 2 * 8 + (tile_index % 8)) * w
        sy = ((tile_index % 256) // 8 % 16) * h
        tile = img.crop((sx, sy, sx + w, sy + h))
        canvas.paste(tile, (dx, dy), tile)

    def _draw_autotile(self, canvas, images, tile_id, dx, dy, animation_frame=0):
        kind = (tile_id - TILE_ID_A1) // 48
        shape = (tile_id - TILE_ID_A1) % 48
        tx = kind % 8
        ty = kind // 8
        set_number = 0
        bx = 0
        by = 0
        table = FLOOR_AUTOTILE_TABLE

        if _is_tile_a1(tile_id):
            water_surface_index = [0, 1, 2, 1][animation_frame % 4]
            if kind == 0:
                bx = water_surface_index * 2
                by = 0
            elif kind == 1:
                bx = water_surface_index * 2
                by = 3
            elif kind == 2:
                bx = 6
                by = 0
            elif kind == 3:
                bx = 6
                by = 3
            else:
                bx = (kind // 4) * 8
                by = ty * 6 + ((kind // 2) % 2) * 3
                if kind % 2 == 0:
                    bx += water_surface_index * 2
                else:
                    bx += 6
                    table = WATERFALL_AUTOTILE_TABLE
                    by += animation_frame % 3
        elif _is_tile_a2(tile_id):
            set_number = 1
            bx = tx * 2
            by = (ty - 2) * 3
        elif _is_tile_a3(tile_id):
            set_number = 2
            bx = tx * 2
            by = (ty - 6) * 2
            table = WALL_AUTOTILE_TABLE
        elif _is_tile_a4(tile_id):
            set_number = 3
            bx = tx * 2
            by = int((ty - 10) * 2.5 + (0.5 if ty % 2 == 1 else 0))
            if ty % 2 == 1:
                table = WALL_AUTOTILE_TABLE

        img = images[set_number]
        if img is None:
            return
        w1 = self.tile_width // 2
        h1 = self.tile_height // 2
        for i in range(4):
            qsx, qsy = table[shape][i]
            sx1 = (bx * 2 + qsx) * w1
            sy1 = (by * 2 + qsy) * h1
            dx1 = dx + (i % 2) * w1
            dy1 = dy + (i // 2) * h1
            quad = img.crop((sx1, sy1, sx1 + w1, sy1 + h1))
            canvas.paste(quad, (dx1, dy1), quad)

    def _fit_canvas(self, canvas, target_size):
        """Scale the map to fill the target size, cropping to avoid black bars."""
        tw, th = target_size
        if canvas.width == 0 or canvas.height == 0:
            return canvas
        scale = max(tw / canvas.width, th / canvas.height)
        new_w = max(1, int(canvas.width * scale))
        new_h = max(1, int(canvas.height * scale))
        resized = canvas.resize((new_w, new_h), Image.Resampling.LANCZOS)
        left = (resized.width - tw) // 2
        top = (resized.height - th) // 2
        return resized.crop((left, top, left + tw, top + th))


def _is_visible_tile(tile_id):
    return 0 < tile_id < TILE_ID_MAX


def _is_autotile(tile_id):
    return tile_id >= TILE_ID_A1


def _is_tile_a1(tile_id):
    return TILE_ID_A1 <= tile_id < TILE_ID_A2


def _is_tile_a2(tile_id):
    return TILE_ID_A2 <= tile_id < TILE_ID_A3


def _is_tile_a3(tile_id):
    return TILE_ID_A3 <= tile_id < TILE_ID_A4


def _is_tile_a4(tile_id):
    return TILE_ID_A4 <= tile_id < TILE_ID_MAX


def _is_tile_a5(tile_id):
    return TILE_ID_A5 <= tile_id < TILE_ID_A1
