import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import google.generativeai as genai
import urllib.parse
import os
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

# --- INITIALIZE MEMORY STATE ---
if 'current_strategy' not in st.session_state:
    st.session_state['current_strategy'] = None
if 'current_prompt' not in st.session_state:
    st.session_state['current_prompt'] = None
if 'render_image' not in st.session_state:
    st.session_state['render_image'] = False

# 2. API CONFIG
load_dotenv()
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-3.5-flash') 
else:
    st.error("❌ GEMINI API KEY MISSING.")

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

# 4. AI FUNCTIONS
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
        response = model.generate_content(prompt, generation_config=genai.GenerationConfig(max_output_tokens=1500, temperature=0.7))
        raw_text = response.text.strip()
        
        if "|||" in raw_text:
            strategy_part, image_part = raw_text.split("|||", 1)
            return {"strategy": strategy_part.strip(), "image_prompt": image_part.strip()}
        else:
            return {"strategy": raw_text, "image_prompt": f"Professional product photography representing the trend: {trend}"}
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower():
            st.error("⏳ **Gemini Speed Limit Reached (5 requests/min).** Please wait 30 seconds before clicking generate again.")
        else:
            st.error(f"🧬 Gemini Error: {e}")
        return None

# 5. UI - TWO STEP PROCESS
col1, col2 = st.columns([1, 2], gap="large")

with col1:
    trend = st.selectbox("Trend", top_trends_list, index=0)
    channel = st.text_input("Partner", value=best_channel, disabled=True)
    
    if st.button("🚀 Generate Campaign Strategy", type="primary", use_container_width=True):
        with st.spinner("🧠 Strategizing with Gemini..."):
            res = fetch_campaign(trend, channel)
            if res:
                st.session_state['current_strategy'] = res.get("strategy")
                st.session_state['current_prompt'] = res.get("image_prompt").replace('"', "'")
                st.session_state['render_image'] = False

with col2:
    if st.session_state['current_strategy']:
        st.markdown(st.session_state['current_strategy'])
        st.divider()
        
        if st.session_state['current_prompt']:
            if not st.session_state['render_image']:
                if st.button("🎨 Paint Concept Art", use_container_width=True):
                    st.session_state['render_image'] = True
                    st.rerun()
            
            if st.session_state['render_image']:
                clean_ai_prompt = urllib.parse.quote(st.session_state['current_prompt'])
                clean_trend = urllib.parse.quote(f"{trend} tools")
                
                ai_url = f"https://image.pollinations.ai/prompt/{clean_ai_prompt}?width=1200&height=600&nologo=true"
                fallback_url = f"https://loremflickr.com/1200/600/{clean_trend}"
                
                js_code = f"""
                <div id="wrapper" style="text-align: center; font-family: sans-serif; color: white;">
                    <p id="loader" style="background: #333; padding: 10px; border-radius: 5px;">⏳ Painting Concept Art... Please wait.</p>
                    <img id="display-img" src="{ai_url}" style="width: 100%; border-radius: 8px; display: none; box-shadow: 0 4px 8px rgba(0,0,0,0.2);" />
                </div>
                <script>
                    const img = document.getElementById("display-img");
                    const loader = document.getElementById("loader");
                    
                    img.onload = function() {{
                        loader.style.display = "none";
                        img.style.display = "block";
                    }};
                    
                    img.onerror = function() {{
                        img.src = "{fallback_url}";
                    }};
                </script>
                """
                components.html(js_code, height=650)
