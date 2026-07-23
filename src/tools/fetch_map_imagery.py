"""One-off fetch of NASA satellite imagery for the Overview page's Europe hero.

Run directly: `python -m src.tools.fetch_map_imagery`

Pulls real Blue Marble (daylight) and Black Marble (VIIRS night-lights) imagery from NASA's
public-domain GIBS WMS service — no API key required — crops/stitches it with Pillow, and writes
WebP files into `dashboard/static/`. Those files are then COMMITTED to the repo (see
`docs/data_sources.md`); this script is a dev-only tool, not part of the deployed app, which is
why `requests` and `Pillow` live in `requirements-dev.txt` rather than `requirements.txt`.

Layer identifiers and their TIME dimensions were confirmed against GIBS GetCapabilities before
writing this script:
  - BlueMarble_NextGeneration   — no TIME dimension (single static composite).
  - VIIRS_Black_Marble          — TIME must be one of 2012-01-01 / 2016-01-01; we use the latter.
Both are served from the same `best/wms.cgi` endpoint in either EPSG:4326 (whole-globe,
equirectangular — what the 3D globe hero needs) or EPSG:3857 (Web Mercator — what the flat hero
needs, matching its existing `mercX`/`mercY` projection in `hero_map.py`).
"""

from __future__ import annotations

import math
from pathlib import Path

import requests
from PIL import Image

from src.config import settings

GIBS_4326 = "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"
GIBS_3857 = "https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi"

DAY_LAYER = "BlueMarble_NextGeneration"
NIGHT_LAYER = "VIIRS_Black_Marble"
NIGHT_TIME = "2016-01-01"

OUT_DIR = Path(__file__).resolve().parents[2] / "dashboard" / "static"

# Same Europe window the flat hero's `mercX`/`mercY` projection uses (see hero_assets.py) —
# wider than any viewport needs so the crop is full-bleed at any aspect ratio.
EUROPE_LON = (-25.0, 40.0)
EUROPE_LAT = (33.0, 60.0)
EUROPE_WIDTH_PX = 3072  # height is derived below to match the true Mercator aspect ratio

_EARTH_R = 6378137.0  # metres, Web Mercator sphere radius (EPSG:3857)


def _merc_x(lon: float) -> float:
    return _EARTH_R * math.radians(lon)


def _merc_y(lat: float) -> float:
    return _EARTH_R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def _europe_bbox_3857() -> tuple[float, float, float, float, int]:
    """Return (minx, miny, maxx, maxy, height_px) for the Europe crop at EUROPE_WIDTH_PX wide,
    with height chosen so pixels aren't stretched (Mercator y is nonlinear in latitude)."""
    x0, x1 = _merc_x(EUROPE_LON[0]), _merc_x(EUROPE_LON[1])
    y0, y1 = _merc_y(EUROPE_LAT[0]), _merc_y(EUROPE_LAT[1])
    height = round(EUROPE_WIDTH_PX * (y1 - y0) / (x1 - x0))
    return x0, y0, x1, y1, height


def _get_map(base_url: str, layer: str, bbox: str, srs: str, width: int, height: int,
             time: str | None = None) -> bytes:
    params = {
        "SERVICE": "WMS",
        "VERSION": "1.1.1",
        "REQUEST": "GetMap",
        "LAYERS": layer,
        "STYLES": "",
        "FORMAT": "image/jpeg",
        "SRS": srs,
        "BBOX": bbox,
        "WIDTH": str(width),
        "HEIGHT": str(height),
    }
    if time:
        params["TIME"] = time
    resp = requests.get(base_url, params=params, timeout=120)
    resp.raise_for_status()
    ctype = resp.headers.get("content-type", "")
    if "image" not in ctype:
        raise RuntimeError(f"Expected an image response for {layer}, got {ctype}: {resp.text[:300]}")
    return resp.content


def _save_webp(jpeg_bytes: bytes, out_path: Path, quality: int = 82) -> None:
    img = Image.open(__import__("io").BytesIO(jpeg_bytes)).convert("RGB")
    img.save(out_path, "WEBP", quality=quality)
    size_kb = out_path.stat().st_size / 1024
    print(f"  wrote {out_path.relative_to(settings.PROJECT_ROOT)}  ({img.width}x{img.height}, {size_kb:.0f} KB)")


def fetch_globe_textures() -> None:
    print("Fetching whole-globe equirectangular textures (for the 3D globe hero)...")
    day = _get_map(GIBS_4326, DAY_LAYER, "-180,-90,180,90", "EPSG:4326", 4096, 2048)
    _save_webp(day, OUT_DIR / "earth_day.webp")
    night = _get_map(GIBS_4326, NIGHT_LAYER, "-180,-90,180,90", "EPSG:4326", 4096, 2048, time=NIGHT_TIME)
    _save_webp(night, OUT_DIR / "earth_night.webp")


def fetch_europe_crop() -> None:
    print("Fetching Web-Mercator Europe crop (for the flat hero)...")
    x0, y0, x1, y1, height = _europe_bbox_3857()
    bbox = f"{x0},{y0},{x1},{y1}"
    day = _get_map(GIBS_3857, DAY_LAYER, bbox, "EPSG:3857", EUROPE_WIDTH_PX, height)
    _save_webp(day, OUT_DIR / "europe_day.webp")
    night = _get_map(GIBS_3857, NIGHT_LAYER, bbox, "EPSG:3857", EUROPE_WIDTH_PX, height, time=NIGHT_TIME)
    _save_webp(night, OUT_DIR / "europe_night.webp")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fetch_globe_textures()
    fetch_europe_crop()
    print("Done. Commit the files in dashboard/static/ — they ship with the app.")


if __name__ == "__main__":
    main()
