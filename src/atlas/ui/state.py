"""Session state transitions for the single Atlas Challenge."""

import streamlit as st


NAVIGATION = (
    "Atlas Challenge",
    "Run Monitor",
    "Candidates",
    "Structures",
    "Evidence",
    "Decision Trace",
    "Scientific Notebook",
    "Benchmarks",
    "Methods",
)


def initialize_session() -> None:
    if "atlas_phase" not in st.session_state:
        st.session_state.atlas_phase = "unloaded"
    if "atlas_run" not in st.session_state:
        st.session_state.atlas_run = None
    if "atlas_benchmark" not in st.session_state:
        st.session_state.atlas_benchmark = None
    if "atlas_active_view" not in st.session_state:
        st.session_state.atlas_active_view = "Atlas Challenge"
