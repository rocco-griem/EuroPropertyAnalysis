"""Reusable Streamlit KPI-card layouts, rendered as themed HTML cards (see `theme.inject_css`)."""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st


def _card(label: str, value: str, sub: str = "", accent: bool = False) -> str:
    value_cls = "ep-kpi-value accent" if accent else "ep-kpi-value"
    sub_html = f'<div class="ep-kpi-sub">{html.escape(sub)}</div>' if sub else ""
    return (
        f'<div class="ep-kpi"><div class="ep-kpi-label">{html.escape(label)}</div>'
        f'<div class="{value_cls}">{html.escape(value)}</div>{sub_html}</div>'
    )


def render_summary_cards(summary_df: pd.DataFrame) -> None:
    """Top-line KPI cards: city count, best/worst CAGR, average affordability pressure.

    Expects the columns produced by `analytics.get_summary_table`. No-ops (with a hint) on an
    empty frame, e.g. when every city has been deselected, rather than raising.
    """
    if summary_df.empty:
        st.info("Select at least one city to see summary metrics.")
        return

    best = summary_df.loc[summary_df["cagr_pct"].idxmax()]
    worst = summary_df.loc[summary_df["cagr_pct"].idxmin()]
    avg_affordability = summary_df["avg_affordability_pressure_pct"].mean()

    cards = [
        _card("Cities shown", str(len(summary_df))),
        _card("Highest CAGR", f"{best['cagr_pct']:.1f}%", sub=str(best["city"]), accent=True),
        _card("Lowest CAGR", f"{worst['cagr_pct']:.1f}%", sub=str(worst["city"])),
        _card("Avg affordability pressure", f"{avg_affordability:.1f} pp"),
    ]
    st.markdown(f'<div class="ep-kpi-row">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_data_quality_notes(summary_df: pd.DataFrame) -> None:
    """Surface any per-city data-quality caveats (e.g. a private/appraisal-based source)."""
    flagged = summary_df.dropna(subset=["data_quality_note"])
    if flagged.empty:
        return
    pills = [
        f'<span class="ep-flag">⚠️ <b>{html.escape(str(row["city"]))}</b> '
        f"{html.escape(str(row['data_quality_note']))}</span>"
        for _, row in flagged.iterrows()
    ]
    st.markdown(f"<div>{''.join(pills)}</div>", unsafe_allow_html=True)
