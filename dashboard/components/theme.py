"""Central design system for the dashboard — colors, Plotly template, CSS, headers.

One place to change the look. Every page imports this and calls `inject_css()` once at the
top (right after `st.set_page_config`) so the custom CSS is present before anything renders.

The categorical city palette was validated for the dark chart surface with the `dataviz`
skill's palette validator (9 slots, lightness band + chroma + CVD floor + contrast all pass;
worst adjacent CVD ΔE 9.7 — the 8–12 floor band, which is legal here because every chart
carries a legend and hover tooltip, so a city is never identified by color alone).

M9 (2026-07-23) added Palma/Mallorca as slots 10-11 (`#6f7bd6` indigo, `#a3852c` bronze),
re-validated as an 11-slot palette (worst adjacent CVD ΔE 6.5, same pre-existing pair, still in
the legal floor band). The two new colors were *appended*, not re-sorted in with the rest —
`CANONICAL_CITIES` fixes the original 9's order first and appends any newer places after, so
none of the original 9 cities' colors shift slots.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from src.config import settings

# --- Core tokens -----------------------------------------------------------------------------
PAGE_ICON = "🏙️"

BACKGROUND = "#0B0E14"  # main plane (matches config.toml backgroundColor)
SURFACE = "#161B26"  # cards / widgets / sidebar
SURFACE_RAISED = "#1C2230"  # hover / raised card
ACCENT = "#E8833A"  # warm amber/terracotta
ACCENT_LIGHT = "#F2A65A"  # hover / highlight
TEXT = "#E6E9EF"  # primary ink
TEXT_MUTED = "#8A93A6"  # captions / labels
BORDER = "rgba(255,255,255,0.07)"
GRID = "#212838"
AXIS = "#2E3646"

# Positive/negative deltas (kept distinct from the categorical slots).
GOOD = "#3FB984"
BAD = "#E5635B"

# Fixed categorical order — assign to cities in a deterministic (sorted) order so every city
# keeps the same color on every page. Validated set/order; do not reorder casually. Slots 10-11
# (indigo, bronze) were appended for Palma/Mallorca in M9 — never insert a new color mid-list,
# since that would shift every later city's slot and repaint it.
CITY_COLORS = [
    "#3987e5",  # blue
    "#d9622b",  # orange
    "#2ba3bd",  # cyan
    "#e66767",  # red
    "#199e70",  # teal
    "#9085e9",  # violet
    "#c47f22",  # amber
    "#d55181",  # magenta
    "#4a9e42",  # green
    "#6f7bd6",  # indigo
    "#a3852c",  # bronze
]

# Single-hue amber ramp for sequential (ranked-bar) encoding, light -> dark.
AMBER_SCALE = [
    [0.0, "#7A4A1E"],
    [0.5, "#C97A2E"],
    [1.0, "#F2A65A"],
]

FONT_FAMILY = "Inter, system-ui, -apple-system, 'Segoe UI', sans-serif"


# Canonical, deterministic city order — every known place gets a fixed palette slot, so a city
# keeps the same color no matter which subset is selected or which page it's on. The original 9
# capitals keep their historical alphabetical order (frozen here, not re-derived) so that any
# place added later — regardless of where it sorts alphabetically — is appended after them
# rather than potentially inserted in the middle, which would shift and repaint existing cities.
_ORIGINAL_9_CAPITALS = [
    "Amsterdam",
    "Berlin",
    "Budapest",
    "London",
    "Madrid",
    "Paris",
    "Prague",
    "Vienna",
    "Warsaw",
]
_all_places = sorted(p.city for p in settings.PLACES)
CANONICAL_CITIES = _ORIGINAL_9_CAPITALS + [
    city for city in _all_places if city not in _ORIGINAL_9_CAPITALS
]
_CITY_COLOR = {city: CITY_COLORS[i % len(CITY_COLORS)] for i, city in enumerate(CANONICAL_CITIES)}


def city_color_map(cities: list[str]) -> dict[str, str]:
    """Stable {city: color}: each city's color is fixed by its slot in `CANONICAL_CITIES`,
    independent of the selected subset, so colors never repaint when the selection changes.

    Cities not in the canonical set (shouldn't happen) fall back to a rotating slot by name."""
    out: dict[str, str] = {}
    for city in cities:
        if city in _CITY_COLOR:
            out[city] = _CITY_COLOR[city]
        else:
            out[city] = CITY_COLORS[hash(city) % len(CITY_COLORS)]
    return out


# --- Plotly template -------------------------------------------------------------------------
_TEMPLATE = go.layout.Template()
_TEMPLATE.layout = go.Layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family=FONT_FAMILY, color=TEXT, size=13),
    title=dict(font=dict(color=TEXT, size=16)),
    margin=dict(l=10, r=20, t=30, b=10),
    colorway=CITY_COLORS,
    xaxis=dict(
        gridcolor=GRID,
        zerolinecolor=AXIS,
        linecolor=AXIS,
        tickfont=dict(color=TEXT_MUTED),
        title=dict(font=dict(color=TEXT_MUTED)),
    ),
    yaxis=dict(
        gridcolor=GRID,
        zerolinecolor=AXIS,
        linecolor=AXIS,
        tickfont=dict(color=TEXT_MUTED),
        title=dict(font=dict(color=TEXT_MUTED)),
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_MUTED),
        title=dict(font=dict(color=TEXT_MUTED)),
    ),
    hoverlabel=dict(bgcolor=SURFACE, bordercolor=BORDER, font=dict(color=TEXT, family=FONT_FAMILY)),
)
pio.templates["europroperty"] = _TEMPLATE
pio.templates.default = "europroperty"


def apply_chart_theme(fig: go.Figure) -> go.Figure:
    """Apply the dark template + shared layout polish to a figure."""
    fig.update_layout(
        template="europroperty",
        margin=dict(l=10, r=20, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig


# --- CSS -------------------------------------------------------------------------------------
_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {{ font-family: {FONT_FAMILY}; }}

/* Trim Streamlit chrome for a cleaner canvas */
#MainMenu, header [data-testid="stToolbar"], footer {{ visibility: hidden; }}
.block-container {{ padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1280px; }}

/* Page header band */
.ep-header {{ margin-bottom: 1.4rem; }}
.ep-title {{
    font-size: 2.0rem; font-weight: 700; letter-spacing: -0.02em; color: {TEXT};
    margin: 0 0 0.25rem 0; line-height: 1.15;
}}
.ep-title .ep-accent {{ color: {ACCENT}; }}
.ep-subtitle {{ color: {TEXT_MUTED}; font-size: 0.98rem; max-width: 70ch; margin: 0; }}
.ep-rule {{ height: 3px; width: 52px; background: {ACCENT}; border-radius: 3px; margin: 0.7rem 0 0 0; }}

/* Section subheaders */
h2, h3, [data-testid="stHeading"] h2, [data-testid="stHeading"] h3 {{
    font-weight: 600; letter-spacing: -0.01em; color: {TEXT};
}}

/* KPI cards */
.ep-kpi-row {{ display: flex; gap: 0.9rem; flex-wrap: wrap; margin: 0.4rem 0 0.6rem 0; }}
.ep-kpi {{
    flex: 1 1 0; min-width: 160px; background: {SURFACE};
    border: 1px solid {BORDER}; border-radius: 14px; padding: 1.05rem 1.15rem;
    position: relative; overflow: hidden;
}}
.ep-kpi::before {{
    content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 3px; background: {ACCENT};
    opacity: 0.9;
}}
.ep-kpi-label {{
    color: {TEXT_MUTED}; font-size: 0.72rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.06em; margin-bottom: 0.4rem;
}}
.ep-kpi-value {{
    color: {TEXT}; font-size: 1.75rem; font-weight: 700; line-height: 1.1;
    font-variant-numeric: tabular-nums;
}}
.ep-kpi-value.accent {{ color: {ACCENT_LIGHT}; }}
.ep-kpi-sub {{ color: {TEXT_MUTED}; font-size: 0.78rem; margin-top: 0.2rem; }}

/* Data-quality flag pill */
.ep-flag {{
    display: inline-flex; align-items: center; gap: 0.45rem; background: rgba(232,131,58,0.10);
    border: 1px solid rgba(232,131,58,0.30); color: {TEXT}; border-radius: 999px;
    padding: 0.32rem 0.75rem; font-size: 0.82rem; margin: 0.2rem 0.4rem 0.2rem 0;
}}
.ep-flag b {{ color: {ACCENT_LIGHT}; font-weight: 600; }}

/* Dataframe corners */
[data-testid="stDataFrame"] {{ border-radius: 10px; overflow: hidden; }}
</style>
"""


def inject_css() -> None:
    """Inject the dashboard's custom CSS. Call once at the top of every page."""
    st.markdown(_CSS, unsafe_allow_html=True)


# --- Tables ----------------------------------------------------------------------------------
# Friendly headers + number formatting for the columns produced by the analytics service.
# Only the columns actually present in a given frame are configured; the rest fall through.
_COLUMN_CONFIG = {
    "city": {"label": "City"},
    "country": {"label": "Country"},
    "year": {"label": "Year", "format": "%d"},
    "start_year": {"label": "Start", "format": "%d"},
    "end_year": {"label": "End", "format": "%d"},
    "total_growth_pct": {"label": "Total growth", "format": "%.1f%%"},
    "cagr_pct": {"label": "CAGR", "format": "%.1f%%"},
    "volatility_pct": {"label": "Volatility", "format": "%.1f%%"},
    "yoy_growth_pct": {"label": "YoY growth", "format": "%.1f%%"},
    "risk_adjusted_return": {"label": "Risk-adj. return", "format": "%.2f"},
    "avg_affordability_pressure_pct": {"label": "Affordability pressure", "format": "%.1f pp"},
    "affordability_pressure_pct": {"label": "Affordability pressure", "format": "%.1f pp"},
    "capital_vs_national_gap_pct": {"label": "Capital vs national", "format": "%.1f pp"},
    "property_index_nominal": {"label": "Index (nominal)", "format": "%.1f"},
    "property_index_real": {"label": "Index (real)", "format": "%.1f"},
    "rental_per_sqm": {"label": "Rent (€/m²)", "format": "€%.1f"},
    "latest_rental_per_sqm": {"label": "Latest rent (€/m²)", "format": "€%.1f"},
    "rental_cagr_pct": {"label": "Rent CAGR", "format": "%.1f%%"},
    "data_quality_note": {"label": "Data-quality note"},
}


def styled_dataframe(df: "pd.DataFrame") -> None:
    """Render a dataframe with friendly headers, number formatting, and no index.

    Only columns with an entry in `_COLUMN_CONFIG` are shown — a column the analytics service
    returns for filtering/joining purposes only (e.g. `place_type`, `parent`) but that isn't
    meant to be end-user-facing simply doesn't appear, rather than falling through with a raw
    column name. Callers that do want such a column displayed should add it to `_COLUMN_CONFIG`.
    """
    df = df.copy()
    # Blank out empty text cells so the table shows "" rather than a literal "None".
    for col in ("data_quality_note", "country"):
        if col in df.columns:
            df[col] = df[col].fillna("")
    shown_cols = [col for col in df.columns if col in _COLUMN_CONFIG]
    df = df[shown_cols]
    config = {}
    for col in shown_cols:
        spec = _COLUMN_CONFIG[col]
        if "format" in spec:
            config[col] = st.column_config.NumberColumn(spec["label"], format=spec["format"])
        else:
            config[col] = st.column_config.Column(spec["label"])
    st.dataframe(df, hide_index=True, width="stretch", column_config=config)


def page_header(title: str, subtitle: str | None = None, accent_word: str | None = None) -> None:
    """Render a consistent title band. If `accent_word` is given, that word is tinted amber."""
    shown = title
    if accent_word and accent_word in title:
        shown = title.replace(accent_word, f'<span class="ep-accent">{accent_word}</span>', 1)
    sub = f'<p class="ep-subtitle">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f'<div class="ep-header"><h1 class="ep-title">{shown}</h1>{sub}'
        f'<div class="ep-rule"></div></div>',
        unsafe_allow_html=True,
    )
