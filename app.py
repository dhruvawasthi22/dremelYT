import streamlit as st
import streamlit.components.v1 as components

# Set up a completely blank, wide canvas
st.set_page_config(page_title="Dremel Trend Dashboard", layout="wide")

# CSS to hide the default Streamlit borders and menus so Looker takes over the whole screen
st.markdown("""
<style>
header {visibility: hidden !important;}
.block-container {
    padding-top: 0rem !important;
    padding-bottom: 0rem !important;
    padding-left: 0rem !important;
    padding-right: 0rem !important;
    margin: 0rem !important;
    max-width: 100% !important;
}
iframe {
    display: block;
    border: none;
}
</style>
""", unsafe_allow_html=True)

# --- PASTE YOUR LOOKER STUDIO EMBED URL BELOW ---
looker_url = "https://datastudio.google.com/embed/reporting/81450734-233d-4c12-b61c-17770e06360b/page/VxqzF"

# Render the Looker Studio dashboard inside your Streamlit site
components.iframe(looker_url, width=None, height=1200, scrolling=False)
