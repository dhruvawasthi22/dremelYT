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
    model = genai.GenerativeModel('gemini-flash-latest')
else:
    st.error("❌ GEMINI_API_KEY missing. Please add it to your Streamlit Cloud Secrets.")

# 3. FETCH LIVE DATA (The Pandas Integration)
# 3. FETCH LIVE DATA (The Pandas Multi-Tab Integration)
@st.cache_data(ttl=3600)
def load_live_data():
    # Notice we changed "format=csv" to "format=xlsx" at the end of the URL
    data_url = "https://docs.google.com/spreadsheets/d/1MtzB35dorD9YUHLlVzfratj27gcdmn2XTZLoVzCIl68/export?format=xlsx"
    
    try:
        # sheet_name=None forces Pandas to load ALL tabs into a dictionary
        sheets = pd.read_excel(data_url, sheet_name=None)
        
        # Extract the exact two tabs you named
        videos_df = sheets['Latest_Videos']
        trends_df = sheets['Trends_History']
        
        return videos_df, trends_df
        
    except Exception as e:
        st.warning(f"⚠️ Could not load live data. Error: {e}")
        # Fallback data matching your exact column names just in case
        fallback_videos = pd.DataFrame({
            "channel": ["Project Farm", "Odd Builds", "Gabi Jones"],
            "engagement_score": [55000, 120000, 45000]
        })
        fallback_trends = pd.DataFrame({
            "trend_phrase": ["Furniture Makeover", "Resin Art", "PC Case Mod"],
            "adjusted_yake_score": [12.5, 9.2, 8.4]
        })
        return fallback_videos, fallback_trends

# Unpack the two separate dataframes
videos_df, trends_df = load_live_data()

# 4. CALCULATE THE #1 TREND AND #1 CHANNEL USING YOUR SCHEMA
# Grabs the highest adjusted_yake_score from the Trends tab
top_trends_list = trends_df.sort_values(by="adjusted_yake_score", ascending=False)["trend_phrase"].unique().tolist()

# Grabs the highest engagement_score from the Videos tab
best_channel = videos_df.sort_values(by="engagement_score", ascending=False).iloc[0]["channel"]

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_campaign_from_ai(target_trend, target_channel):
    import time
    import json
    
    optimized_prompt = f"""
    Act as Dremel CMO. Target: 24-44. Voice: resourceful. 
    Create a concise campaign for trend: '{target_trend}', partner: '{target_channel}'.
    Return ONLY valid JSON format:
    {{
        "strategy": "Markdown text. Bold headings: 1. SEO 2. Email 3. Ad Copy 4. UGC 5. CTA.",
        "image_prompt": "Cinematic 4k Stable Diffusion prompt for {target_trend} using Dremel."
    }}
    """
    
    safety_config = genai.types.GenerationConfig(
        max_output_tokens=800,
        temperature=0.7
    )
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(optimized_prompt, generation_config=safety_config)
            clean_json = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
            
        except Exception as e:
            if "429" in str(e) or "Quota" in str(e):
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
            return None

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
            with st.spinner(f"🧠 Analyzing '{selected_trend}'... (This is instant if previously cached)"):
                
                result = fetch_campaign_from_ai(selected_trend, selected_channel)
                
                if result is None:
                    st.error("❌ Google AI Quota Exceeded. The API is too busy. Please try again in a few seconds.")
                else:
                    strategy_text = result.get("strategy", "Strategy generation failed.")
                    dynamic_image_prompt = result.get("image_prompt", f"Cinematic product photography of {selected_trend}")
                    
                    import urllib.parse
                    safe_url_prompt = urllib.parse.quote(dynamic_image_prompt)
                    image_url = f"https://image.pollinations.ai/prompt/{safe_url_prompt}?width=1200&height=600&nologo=true"
                    
                    st.image(image_url, caption=f"AI Concept Art: {dynamic_image_prompt}", use_container_width=True)
                    st.markdown(strategy_text)
