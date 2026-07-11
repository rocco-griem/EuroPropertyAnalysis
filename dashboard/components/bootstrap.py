"""One-time database bootstrap, shared by every dashboard page.

A Streamlit multipage app is still a single server process, so `st.cache_resource` state
(and therefore this check) is shared across pages — whichever page a user lands on first
triggers it, and every other page's call is then a cheap cache hit.
"""

from __future__ import annotations

import streamlit as st
from sqlalchemy import func, select

from src.database.connection import get_session, init_db
from src.database.models import SummaryMetric
from src.pipeline.real_pipeline import run_real_pipeline


@st.cache_resource
def ensure_database() -> None:
    """Create tables and populate them with the real pipeline data if the database is empty."""
    init_db()
    with get_session() as session:
        row_count = session.execute(select(func.count()).select_from(SummaryMetric)).scalar_one()
    if row_count == 0:
        run_real_pipeline()
