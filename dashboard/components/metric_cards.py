"""Reusable Streamlit KPI-card layouts, built on `st.metric`."""

from __future__ import annotations

import pandas as pd
import streamlit as st


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

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Cities shown", len(summary_df))
    col2.metric(f"Highest CAGR — {best['city']}", f"{best['cagr_pct']:.1f}%")
    col3.metric(f"Lowest CAGR — {worst['city']}", f"{worst['cagr_pct']:.1f}%")
    col4.metric("Avg affordability pressure", f"{avg_affordability:.1f} pp")


def render_data_quality_notes(summary_df: pd.DataFrame) -> None:
    """Surface any per-city data-quality caveats (e.g. a private/appraisal-based source)."""
    flagged = summary_df.dropna(subset=["data_quality_note"])
    for _, row in flagged.iterrows():
        st.caption(f"⚠️ **{row['city']}**: {row['data_quality_note']}")
