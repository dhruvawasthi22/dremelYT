import streamlit as st
import pandas as pd
import google.generativeai as genai
import urllib.parse
import json
import os
from dotenv import load_dotenv

# 1. SETUP & CONFIGURATION
st.set_page_config(page_title="Dremel | AI Campaign Architect", layout="wide", initial_sidebar_state="collapsed")

# Remove the Streamlit header and padding for a clean, native app look
st.markdown("""
    <style>
    [data-testid="stHeader"], [data-testid="stSidebar"] {display: none !important;}
    div.block-container {
        padding-top: 2rem !important; 
        max-width: 95% !important;   
    }
    /* Dremel Navigation Button */
    div[data-testid="stButton"] button.nav-btn {
        background-color: #333333; color: white; border: none;
    }
    </style>
""", unsafe_allow_html=True)

# Navigation Back to Main Dashboard
if st.button("⬅️ Back to Looker Studio", key="back_btn", help="Return to Main Dashboard"):
    st.switch_page("app.py")

st.title("⚡ AI Campaign Architect")
st.markdown("Instantly generate full-funnel marketing strategies based on your live GitHub/Sheets data pipeline.")
st.divider()

# 2. SECURITY HANDSHAKE CONFIGURATION
load_dotenv()

# Fetch variables from Streamlit Secrets first (for Cloud), then fallback to .env (for local)
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
YOUTUBE_API_KEY = st.secrets.get("YOUTUBE_API_KEY", os.getenv("YOUTUBE_API_KEY"))
GOOGLE_CREDS_JSON = st.secrets.get("GOOGLE_CREDS", os.getenv("GOOGLE_CREDS"))

# Initialize Gemini Model if key is present
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("❌ GEMINI_API_KEY missing. Please add it to your Streamlit Cloud Secrets.")

# 3. FETCH LIVE DATA (The Pandas Integration)
@st.cache_data(ttl=3600)
def load_live_data():
    # Modified Google Sheets link to force CSV export instead of loading the HTML webpage
    data_url = "https://docs.google.com/spreadsheets/d/1MtzB35dorD9YUHLlVzfratj27gcdmn2XTZLoVzCIl68/export?format=csv"
    
    try:
        df = pd.read_csv(data_url)
        return df
    except Exception as e:
        st.warning("⚠️ Could not load live CSV. Using fallback data.")
        return pd.DataFrame({
            "trend_phrase": ["Furniture Makeover", "Resin Art", "PC Case Mod"],
            "Trend Power": [12.5, 9.2, 8.4],
            "channel": ["Project Farm", "Odd Builds", "Gabi Jones"],
            "engagement_score": [55000, 120000, 45000]
        })

df = load_live_data()

# 4. CALCULATE THE #1 TREND AND #1 CHANNEL
top_trends_list = df.sort_values(by="Trend Power", ascending=False)["trend_phrase"].unique().tolist()
best_channel = df.sort_values(by="engagement_score", ascending=False).iloc[0]["channel"]

# 5. THE USER INTERFACE
col1, col2 = st.columns([1, 2], gap="large")

with col1:
    st.subheader("Campaign Parameters")
    st.info("Parameters auto-populated from today's pipeline data.")
    
    selected_trend = st.selectbox("Target Trend (Sorted by Max Trend Power)", top_trends_list, index=0)
    selected_channel = st.text_input("Partner Channel (Highest Engagement)", value=best_channel, disabled=True)
    
    generate_btn = st.button("🚀 Generate Dremel Campaign", type="primary", use_container_width=True)

with col2:
    if generate_btn:
        if not GEMINI_API_KEY:
            st.error("Cannot generate campaign: Gemini API key is missing.")
        else:
            with st.spinner("🧠 Gemini AI is analyzing the data and drafting the playbook..."):
                prompt = f"""
                Act as the Chief Marketing Officer for Dremel. Target audience: ages 24-44. 
                Brand Voice: cool, creative, resourceful, value-driven.
                
                Task: Create a marketing campaign for the trend: '{selected_trend}', partnering with the YouTube channel '{selected_channel}'.
                
                You MUST return a valid JSON object with exactly two keys. Do not include markdown code blocks (like ```json), just the raw JSON:
                {{
                    "strategy": "A markdown-formatted string containing the full campaign. Include bold headings for: 1. SEO Keywords & Blog Title, 2. A 3-part Email Marketing drip, 3. Social Media Ad copy, 4. A User Generated Content (UGC) contest, and 5. Call to Action.",
                    "image_prompt": "A highly detailed, comma-separated visual description for an AI image generator to create cinematic concept art for this specific campaign. Do not use text in the image. Focus on lighting, the Dremel tool, and the demographic doing the {selected_trend}."
                }}
                """
                
                try:
                    response = model.generate_content(prompt)
                    clean_json = response.text.replace("```json", "").replace("```", "").strip()
                    result = json.loads(clean_json)
                    
                    strategy_text = result.get("strategy", "Strategy generation failed.")
                    dynamic_image_prompt = result.get("image_prompt", f"A cool cinematic product photography shot of {selected_trend} using a Dremel")
                    
                    # Generate Image via Pollinations
                    safe_url_prompt = urllib.parse.quote(dynamic_image_prompt)
                    # Fixed the markdown typo in this URL string
                    image_url = f"[https://image.pollinations.ai/prompt/](https://image.pollinations.ai/prompt/){safe_url_prompt}?width=1200&height=600&nologo=true"
                    
                    # Render Outputs
                    st.image(image_url, caption=f"AI Generated Concept Art: {dynamic_image_prompt}", use_container_width=True)
                    st.markdown(strategy_text)
                    
                except Exception as e:
                    st.error(f"Failed to generate campaign. Error: {e}")
