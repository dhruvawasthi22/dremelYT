import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Set page configurations with a clean canvas
st.set_page_config(page_title="MakerTrends | Power Tool Intelligence", layout="wide")

# Custom Strict Palette CSS Injector (White, #014692 Blue, Black Text)
# Custom Strict Palette CSS Injector (White, #014692 Blue, Black Text)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    /* Global Container Fixes */
    .main { background-color: #ffffff; font-family: 'Inter', sans-serif; color: #000000; }
    /* FIXED: Increased padding-top from 1.5rem to 4rem to clear the Streamlit top menu */
    .block-container { padding-top: 4rem !important; padding-bottom: 2rem !important; }
    
    /* Global Text Adjustments to Force True Black */
    p, span, label, sm, div { color: #000000 !important; }
    
    /* Header Branding Layout */
    /* FIXED: Added line-height buffer to prevent internal text clipping */
    .brand-title { color: #014692 !important; font-weight: 800; font-size: 2.25rem; letter-spacing: -0.5px; line-height: 1.3; }
    .brand-subtitle { color: #444444 !important; font-size: 1rem; margin-bottom: 1.5rem; margin-top: 5px; }
    .accent-bar { width: 100%; height: 4px; background-color: #014692; border-radius: 2px; margin-bottom: 2.5rem; }
    
    /* Card Elements styled for the new theme */
    .metric-card { background: #ffffff; padding: 24px; border-radius: 6px; box-shadow: 0 4px 16px rgba(1, 70, 146, 0.06); border: 1px solid #e1e8ed; border-top: 5px solid #014692; }
    .metric-title { color: #444444 !important; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
    .metric-value { color: #014692 !important; font-size: 2rem; font-weight: 800; line-height: 1; }
    
    /* Section Headers */
    .section-header { color: #014692 !important; font-weight: 700; font-size: 1.4rem; margin-top: 1.5rem; margin-bottom: 4px; }
    .section-caption { color: #444444 !important; font-size: 0.9rem; margin-bottom: 1.5rem; }
    
    /* Video Feed Rows */
    .video-card { background: #ffffff; padding: 20px; border-radius: 6px; border: 1px solid #e1e8ed; box-shadow: 0 2px 6px rgba(0,0,0,0.01); margin-bottom: 12px; }
    .video-title a { color: #014692 !important; font-weight: 600; font-size: 1.1rem; text-decoration: none; }
    .video-title a:hover { text-decoration: underline; }
    .video-meta { color: #444444 !important; font-size: 0.85rem; margin-top: 4px; }
    .video-stat-label { color: #444444 !important; font-size: 0.75rem; text-transform: uppercase; font-weight: 600; }
    .video-stat-value { color: #000000 !important; font-size: 1.25rem; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

# Helper function to load data safely
@st.cache_data(ttl=600)
def load_data():
    history_file = "youtube_power_tool_trends_history.csv"
    videos_file = "youtube_power_tool_videos.csv"
    
    hist_df = pd.read_csv(history_file) if os.path.exists(history_file) else pd.DataFrame(columns=["run_date", "trend_phrase", "yake_score"])
    vid_df = pd.read_csv(videos_file) if os.path.exists(videos_file) else pd.DataFrame()
    
    if not hist_df.empty:
        hist_df["run_date"] = pd.to_datetime(hist_df["run_date"])
        hist_df["relevance_score"] = 1 / (hist_df["yake_score"] + 0.001)
    return hist_df, vid_df

hist_df, vid_df = load_data()

# --- HEADER BRANDING (Dynamically switches to image file if found in root directory) ---
icon_path = "dremel_icon.png"

if os.path.exists(icon_path):
    h_col1, h_col2 = st.columns([1, 24])
    with h_col1:
        st.image(icon_path, width=44)
    with h_col2:
        st.markdown('<div class="brand-title" style="margin-top: -3px;">MAKER TRENDS INTEL</div>', unsafe_allow_html=True)
else:
    # Safe fallback layout in case file hasn't been uploaded yet
    st.markdown('<div class="brand-title">MAKER TRENDS INTEL</div>', unsafe_allow_html=True)

st.markdown('<div class="brand-subtitle">Real-time telemetry and search phrase discovery extracted from creator video metadata.</div>', unsafe_allow_html=True)
st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)

if hist_df.empty or vid_df.empty:
    st.error("Data tracking files not found. Run your data_pipeline.py architecture inside GitHub Actions to generate initial records.")
    st.stop()

# --- KPI METRICS GRID ---
latest_date = hist_df["run_date"].max()
today_trends = hist_df[hist_df["run_date"] == latest_date]
top_overall_phrase = today_trends.sort_values("relevance_score", ascending=False).iloc[0]["trend_phrase"] if not today_trends.empty else "N/A"

m1, m2, m3 = st.columns(3)
with m1:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Telemetry Run Date</div><div class="metric-value">{latest_date.strftime("%Y-%m-%d")}</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Spiking Key-phrase</div><div class="metric-value" style="color: #014692 !important;">{top_overall_phrase.upper()}</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Monitored Creators</div><div class="metric-value">{vid_df["channel"].nunique():,}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- VISUALIZATION MATRICES ---
c_left, c_right = st.columns([1, 1])

with c_left:
    st.markdown('<div class="section-header">Maximum Occurring Trend Matrix</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-caption">Bubble graph mapping tracking metrics. Size correlates directly with total phrase occurrences.</div>', unsafe_allow_html=True)
    
    # Process occurrence totals explicitly for bubble size configuration
    bubble_data = hist_df.groupby("trend_phrase").agg(
        occurrences=("trend_phrase", "count"),
        avg_relevance=("relevance_score", "mean")
    ).reset_index().sort_values("occurrences", ascending=False).head(15)
    
    fig_bubble = px.scatter(
        bubble_data, 
        x="avg_relevance", 
        y="occurrences", 
        text="trend_phrase",
        size="occurrences",        # Bubble size perfectly driven by frequency count
        color="occurrences",       
        size_max=45,               
        color_continuous_scale=["#9cc2ef", "#014692"], 
        labels={"avg_relevance": "Average Relevance Weight", "occurrences": "Total Recorded Occurrences"}
    )
    
    fig_bubble.update_traces(
        textposition='top center', 
        marker=dict(line=dict(width=1.5, color='#ffffff'))
    )
    fig_bubble.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", 
        paper_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False, 
        margin=dict(t=15, b=15, l=15, r=15),
        xaxis=dict(showgrid=True, gridcolor="#eef1f5", zeroline=False, title_font=dict(color="black"), tickfont=dict(color="black")),
        yaxis=dict(showgrid=True, gridcolor="#eef1f5", zeroline=False, title_font=dict(color="black"), tickfont=dict(color="black"))
    )
    st.plotly_chart(fig_bubble, use_container_width=True, config={'displayModeBar': False})

with c_right:
    st.markdown('<div class="section-header">Historical Timeline Trajectory</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-caption">Select tracked phrases to isolate their performance over time.</div>', unsafe_allow_html=True)
    
    unique_phrases = sorted(hist_df["trend_phrase"].unique())
    selected_phrases = st.multiselect("Isolate Data Streams:", unique_phrases, default=unique_phrases[:2], label_visibility="collapsed")
    
    if selected_phrases:
        timeline_df = hist_df[hist_df["trend_phrase"].isin(selected_phrases)].sort_values("run_date")
        fig_line = px.line(
            timeline_df, x="run_date", y="relevance_score", color="trend_phrase",
            color_discrete_sequence=["#014692", "#5593d8", "#002244", "#88bbee"]
        )
        fig_line.update_traces(line=dict(width=3.5), marker=dict(size=6))
        fig_line.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=25, b=10, l=10, r=10), showlegend=True, legend_title=None,
            xaxis=dict(showgrid=True, gridcolor="#eef1f5", title=None, tickfont=dict(color="black")),
            yaxis=dict(showgrid=True, gridcolor="#eef1f5", title=None, tickfont=dict(color="black"))
        )
        st.plotly_chart(fig_line, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("Select specific phrases above to render historical trend timelines.")

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown('<div class="section-header">Targeted Content Explorer</div>', unsafe_allow_html=True)
st.markdown('<div class="section-caption">Isolate specific keywords to identify high-performing content drivers.</div>', unsafe_allow_html=True)

selected_trend = st.selectbox("Filter Target Video Index:", unique_phrases, label_visibility="collapsed")

def matches_trend(row, phrase):
    target_pool = f"{row.get('title', '')} {row.get('description', '')} {row.get('tags', '')}".lower()
    return all(word in target_pool for word in phrase.lower().split())

if selected_trend:
    matched_mask = vid_df.apply(lambda row: matches_trend(row, selected_trend), axis=1)
    matched_vids = vid_df[matched_mask].sort_values("engagement_score", ascending=False)
    
    if not matched_vids.empty:
        for _, row in matched_vids.head(10).iterrows():
            st.markdown(f"""
                <div class="video-card">
                    <table style="width:100%; border-collapse:collapse; border:none; background:none;">
                        <tr style="border:none; background:none;">
                            <td style="width:75%; border:none; padding:0; vertical-align:top;">
                                <div class="video-title"><a href="{row['video_link']}" target="_blank">{row['title']}</a></div>
                                <div class="video-meta">Creator: <strong>{row['channel']}</strong> &nbsp;|&nbsp; Published: {str(row['published_at'])[:10]}</div>
                            </td>
                            <td style="width:12.5%; border:none; padding:0; text-align:center; vertical-align:middle;">
                                <div class="video-stat-label">Raw Views</div>
                                <div class="video-stat-value">{int(row['view_count']):,}</div>
                            </td>
                            <td style="width:12.5%; border:none; padding:0; text-align:center; vertical-align:middle;">
                                <div class="video-stat-label">Engagement</div>
                                <div class="video-stat-value">{int(row['engagement_score']):,}</div>
                            </td>
                        </tr>
                    </table>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No active video records contain this exact keyword pattern.")
