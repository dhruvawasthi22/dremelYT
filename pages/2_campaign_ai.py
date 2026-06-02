import streamlit as st
import pandas as pd
import google.generativeai as genai
import urllib.parse
import json
import time
import os
import typing
from dotenv import load_dotenv

# Define strict, un-crashable data structural expectations for the API
class CampaignPlaybook(typing.TypedDict):
    strategy: str
    image_prompt: str

# 1. SETUP
st.set_page_config(page_title="Dremel | AI Campaign Architect", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
    <style>
    [data-testid="stHeader"], [data-testid="stSidebar"] {display: none !important;}
    div.block-container { padding-top: 2rem !important; max-width: 95% !important; }
    div[data-testid="stButton"] button.nav-btn { background-color: #333333; color: white; border: none; }
    </style>
""", unsafe_allow_html=True)

if st.button("⬅️ Dashboard"): st.switch_page("app.py")

try: st.image("dremel_icon.png", width=200)
except: pass

st.title("AI Campaign Architect")
st.divider()

# 2. API CONFIG
load_dotenv()
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-3.5-flash') 
else:
    st.error("❌ API KEY MISSING.")

# 3. DATA
@st.cache_data(ttl=3600)
def load_live_data():
    try:
        sheets = pd.read_excel("https://docs.google.com/spreadsheets/d/1MtzB35dorD9YUHLlVzfratj27gcdmn2XTZLoVzCIl68/export?format=xlsx", sheet_name=None)
        return sheets['Latest_Videos'], sheets['Trends_History']
    except:
        return pd.DataFrame({"channel": ["Project Farm"], "engagement_score": [55000]}), pd.DataFrame({"trend_phrase": ["Furniture Makeover"], "adjusted_yake_score": [12.5]})

videos_df, trends_df = load_live_data()
top_trends_list = trends_df.sort_values(by="adjusted_yake_score", ascending=False)["trend_phrase"].unique().tolist()
best_channel = videos_df.sort_values(by="engagement_score", ascending=False).iloc[0]["channel"]

# 4. AI FUNCTION
@st.cache_data(ttl=86400, show_spinner=False)
def fetch_campaign(trend, channel):
    prompt = f"""
    Act as Dremel CMO. Target audience: 24-44. Voice: resourceful and concise.
    Create a highly condensed campaign blueprint for the trend: '{trend}', partnering with the channel: '{channel}'.
    
    Structure the 'strategy' field text using short markdown bullet blocks covering:
    1. SEO Keywords, 2. Email Copy, 3. Social Ads, 4. UGC Contest. Keep it under 120 words total.
    
    For 'image_prompt', write a single-sentence photography style description for {trend}.
    """
    
    try:
        # Enforcing structured schemas to bypass string token formatting issues
        response = model.generate_content(
            prompt, 
            generation_config=genai.GenerationConfig(
                max_output_tokens=1000, 
                temperature=0.7, 
                response_mime_type="application/json",
                response_schema=CampaignPlaybook # Hard constraint structure
            )
        )
        return json.loads(response.text)
    except Exception as e:
        st.error(f"🧬 Debug Info (Actual API Error): {e}")
        return None

# 5. UI
col1, col2 = st.columns([1, 2], gap="large")

with col1:
    trend = st.selectbox("Trend", top_trends_list, index=0)
    channel = st.text_input("Partner", value=best_channel, disabled=True)
    want_image = st.toggle("Generate Concept Art", value=True)
    btn = st.button("🚀 Generate Campaign", type="primary", use_container_width=True)

with col2:
    if btn:
        with st.spinner("Analyzing..."):
            res = fetch_campaign(trend, channel)
            if res:
                # Render the image container only if the checkbox is active
                if want_image and "image_prompt" in res and res["image_prompt"]:
                    st.image(f"https://image.pollinations.ai/prompt/{urllib.parse.quote(res['image_prompt'])}?width=1200&height=600&nologo=true", use_container_width=True)
                
                st.markdown(res.get("strategy", "Error loading campaign text."))
