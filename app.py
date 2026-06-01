import streamlit as st
import time

# 1. Setup the wide page
st.set_page_config(page_title="MakerTrends | Power Tool Intelligence", layout="wide")

# 2. CSS to kill ALL padding, but leave just enough room at the top for our button
st.markdown("""
    <style>
    [data-testid="stHeader"] {display: none !important;}
    
    div.block-container {
        padding-top: 1rem !important; /* Added 1rem so the button isn't cut off */
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        margin-top: -3rem !important; 
        max-width: 100% !important;   
    }
    
    /* Style the Streamlit button to look corporate and clean */
    div[data-testid="stButton"] button {
        float: right;
        margin-right: 20px;
        background-color: #014692; /* Dremel Blue */
        color: white;
        border-radius: 4px;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Create the Refresh Button UI
col1, col2 = st.columns([9, 1]) # Pushes the button to the far right
with col2:
    if st.button("🔄 Refresh Dashboard"):
        # When clicked, Streamlit will just rapidly re-run this script
        pass 

# 4. Your Looker URL (Base)
looker_url = "https://datastudio.google.com/embed/reporting/81450734-233d-4c12-b61c-17770e06360b/page/VxqzF"

# 5. THE CACHE BUSTER: Append the current time so the browser thinks it's a brand new link
timestamp = int(time.time())
cache_busting_url = f"{looker_url}?t={timestamp}"

# 6. Injecting the iframe
st.markdown(f"""
    <iframe src="{cache_busting_url}" width="100%" height="1200" style="border:none; padding:0; margin:0;"></iframe>
""", unsafe_allow_html=True)
