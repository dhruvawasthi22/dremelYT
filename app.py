import streamlit as st
import streamlit.components.v1 as components

# Set up a completely blank, wide canvas
st.set_page_config(page_title="Dremel Trend Dashboard", layout="wide")

# CSS to hide the default Streamlit borders and menus so Looker takes over the whole screen
st.markdown("""
    <style>
    /* 1. Hide the top header entirely */
    [data-testid="stHeader"] {
        display: none !important;
    }
    
    /* 2. Remove padding from the main app container */
    [data-testid="stAppViewContainer"] {
        padding: 0px !important;
        margin: 0px !important;
    }
    
    /* 3. Target the specific internal block where your code actually renders */
    [data-testid="block-container"], 
    [data-testid="stAppViewBlockContainer"] {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        max-width: 100% !important;
    }

    /* 4. Strip away any default iframe margins or spacing */
    iframe {
        display: block !important;
        border: none !important;
        margin: 0px !important;
        padding: 0px !important;
    }
    </style>
""", unsafe_allow_html=True)
# --- PASTE YOUR LOOKER STUDIO EMBED URL BELOW ---
looker_url = "https://datastudio.google.com/embed/reporting/81450734-233d-4c12-b61c-17770e06360b/page/VxqzF"

# Render the Looker Studio dashboard inside your Streamlit site
components.iframe(looker_url, width=None, height=1200, scrolling=False)
