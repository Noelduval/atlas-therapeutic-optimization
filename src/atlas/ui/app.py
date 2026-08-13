"""Atlas v1 Streamlit entrypoint."""

import streamlit as st

from atlas.ui.state import NAVIGATION, initialize_session
from atlas.ui.styles import APP_CSS
from atlas.ui.views import render_challenge, render_selected_view


st.set_page_config(
    page_title="Atlas Challenge",
    page_icon="A",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(APP_CSS, unsafe_allow_html=True)
initialize_session()


def _select_mobile_view() -> None:
    selected_view = st.session_state.atlas_mobile_navigation
    st.session_state.atlas_active_view = selected_view
    st.session_state.atlas_sidebar_navigation = selected_view


def _select_sidebar_view() -> None:
    selected_view = st.session_state.atlas_sidebar_navigation
    st.session_state.atlas_active_view = selected_view
    st.session_state.atlas_mobile_navigation = selected_view


st.selectbox(
    "View",
    NAVIGATION,
    key="atlas_mobile_navigation",
    on_change=_select_mobile_view,
)

with st.sidebar:
    st.markdown('<div class="atlas-wordmark">Atlas</div>', unsafe_allow_html=True)
    st.radio(
        "Navigation",
        NAVIGATION,
        label_visibility="collapsed",
        key="atlas_sidebar_navigation",
        on_change=_select_sidebar_view,
    )

st.markdown(
    """
    <style>
    div[data-testid="stSelectbox"] { display: none; }
    @media (max-width: 700px) {
      [data-testid="stSidebar"] { display: none !important; }
      div[data-testid="stSelectbox"] { display: block; max-width: 100%; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if st.session_state.atlas_phase != "complete":
    render_challenge()
else:
    render_selected_view(st.session_state.atlas_active_view, st.session_state.atlas_run)
