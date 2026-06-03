import streamlit as st
import pandas as pd
import google.generativeai as genai
import urllib.parse
import os
import requests
from dotenv import load_dotenv

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
    Act as Dremel CMO. Target audience: 24-44. Voice: professional, resourceful, and action-oriented.
    Create a complete campaign blueprint for the trend: '{trend}', partnering with the channel: '{channel}'.
    
    You must output exactly two main components separated by the divider '|||'.
    
    Component 1: Complete the following four marketing points fully. Do not leave any point empty or incomplete.
    1. SEO Keywords: List 4 relevant search terms.
    2. Email Copy: Write a concise subject line and a 2-sentence promotional hook.
    3. Social Ads: Provide a strong headline and primary text copy block.
    4. UGC Contest: Outline a quick call-to-action campaign mechanic for users.
    
    |||
    
    Component 2: Write a detailed, single-sentence photography style description to use as an AI image generation prompt for this trend.
    """
    
    try:
        response = model.generate_content(
            prompt, 
            generation_config=genai.GenerationConfig(
                max_output_tokens=1500, 
                temperature=0.7
            )
        )
        
        raw_text = response.text.strip()
        
        # Safe split handling to guarantee content display
        if "|||" in raw_text:
            strategy_part, image_part = raw_text.split("|||", 1)
            return {
                "strategy": strategy_part.strip(),
                "image_prompt": image_part.strip()
            }
        else:
            return {
                "strategy": raw_text,
                "image_prompt": f"Professional photography of {trend}, studio lighting, highly detailed."
            }
            
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
                if want_image and res.get("image_prompt"):
                    
                    # 1. Format the AI Prompt URL
                    clean_ai_prompt = urllib.parse.quote(res["image_prompt"])
                    ai_url = f"https://image.pollinations.ai/prompt/{clean_ai_prompt}?width=1200&height=600&nologo=true"
                    
                    # 2. THE BYPASS: Force the user's browser to load the image via HTML
                    st.markdown(f"""
                        <div style="text-align: center; margin-bottom: 20px;">
                            <img src="{ai_url}" alt="AI Concept Art" style="width: 100%; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                            <p style="color: gray; font-size: 0.9em; margin-top: 10px;">🎨 <b>AI Concept Art:</b> {res['image_prompt']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                # Render the strategy text
                st.markdown(res.get("strategy", "Error loading campaign text."))
