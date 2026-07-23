"""EuroPropertyAnalysis — Streamlit dashboard entry point (navigation router).

Run with: `streamlit run dashboard/app.py`

This file only builds the navigation menu; each page's own logic lives in `views/overview.py` or
`pages/*.py`. Every page reads exclusively through `src.services.analytics` — never raw SQLAlchemy
queries — so the query logic stays testable independent of the UI.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make sibling modules in dashboard/components importable regardless of how the script was
# launched (`streamlit run` adds the script's directory to sys.path, but test runners may not).
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

from components import theme

st.set_page_config(page_title="EuroPropertyAnalysis", page_icon=theme.PAGE_ICON, layout="wide")

pages = [
    st.Page("views/overview.py", title="Overview", icon="🏠", default=True),
    st.Page("pages/1_City_Comparison.py", title="City Comparison", icon="⚖️"),
    st.Page("pages/2_Rankings.py", title="Rankings", icon="🏆"),
    st.Page("pages/3_Affordability.py", title="Affordability", icon="💶"),
    st.Page("pages/5_Rentals.py", title="Rentals", icon="🔑"),
    st.Page("pages/6_Mallorca_Deep_Dive.py", title="Mallorca Deep Dive", icon="🏝️"),
    st.Page("pages/4_Methodology.py", title="Methodology", icon="📖"),
]
pg = st.navigation(pages)

st.sidebar.caption("Data: 2015–2024 · 9 capitals + Palma · deep dive: Mallorca")

pg.run()
