#!/usr/bin/env python3
"""Recolor AIG desktop icon SVGs to the AIG scheme.

- Tile (first path, rounded-square background): #263075 (AIG indigo)
- Glyph (all other paths): #FFFFFF (white)

Run from the app root:  python3 recolor_icons.py
"""
import re
from pathlib import Path

APP_ROOT = Path(__file__).parent
ICON_DIRS = [
    APP_ROOT / "custom_theme" / "public" / "icons" / "desktop_icons" / "solid",
    APP_ROOT / "custom_theme" / "public" / "icons" / "desktop_icons" / "subtle",
]

TILE_FILL = "#263075"
GLYPH_FILL = "#FFFFFF"

# Matches `fill="..."` / `fill='...'` on a path element
FILL_RE = re.compile(r'fill="([^"]*)"')


def recolor(svg: str) -> str:
    # Only explicit, non-inherited fills count: the first is the tile, the rest are glyphs.
    fills = [f for f in FILL_RE.findall(svg) if f.lower() != "none"]
    if not fills:
        return svg
    out = svg
    for i, current in enumerate(fills):
        replacement = TILE_FILL if i == 0 else GLYPH_FILL
        if current != replacement:
            out = out.replace(f'fill="{current}"', f'fill="{replacement}"', 1)
    return out


def main() -> None:
    for icon_dir in ICON_DIRS:
        if not icon_dir.exists():
            continue
        for svg_path in sorted(icon_dir.glob("*.svg")):
            original = svg_path.read_text()
            recolored = recolor(original)
            if recolored != original:
                svg_path.write_text(recolored)
                print(f"recolored {svg_path.relative_to(APP_ROOT)}")
            else:
                print(f"unchanged  {svg_path.relative_to(APP_ROOT)}")


if __name__ == "__main__":
    main()
