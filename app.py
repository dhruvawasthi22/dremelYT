import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Set page configurations with a sleek layout
st.set_page_config(page_title="MakerTrends | Power Tool Intelligence", layout="wide")

# Custom Dremel-inspired CSS Styling Injector
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    h1 { color: #0B2341; font-weight: 800; font-family: 'Helvetica Neue', sans-serif; border-bottom: 3px solid #E35205; padding-bottom: 10px; }
    h2, h3 { color: #0B2341; font-weight: 700; }
    .metric-card { background: white; padding: 20px; border-radius: 6px; border-left: 5px solid #0B2341; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .accent-card { border-left-color: #E35205 !important; }
    </style>
""", unsafe_embed_allowed=True)


# Helper function to load data safely
@st.cache_data(ttl=600)
def load_data():
    history_file = "youtube_power_tool_trends_history.csv"
    videos_file = "youtube_power_tool_videos.csv"

    hist_df = pd.read_csv(history_file) if os.path.exists(history_file) else pd.DataFrame(
        columns=["run_date", "trend_phrase", "yake_score"])
    vid_df = pd.read_csv(videos_file) if os.path.exists(videos_file) else pd.DataFrame()

    # Clean up dates and invert YAKE score so higher values indicate greater relevance
    if not hist_df.empty:
        hist_df["run_date"] = pd.to_datetime(hist_df["run_date"])
        hist_df["relevance_score"] = 1 / (hist_df["yake_score"] + 0.001)
    return hist_df, vid_df


hist_df, vid_df = load_data()

# --- HEADER HEADER SECTION ---
st.markdown("<h1>MAKER TRENDS — PERFORMANCE DASHBOARD</h1>", unsafe_embed_allowed=True)
st.markdown("Real-time telemetry and search phrase discovery extracted from creator video metadata.")

if hist_df.empty or vid_df.empty:
    st.warning(
        "Data files not detected. Ensure your data pipeline script runs completely at least once to populate baseline metrics.")
    st.stop()

# --- KPI METRICS MATRICES ---
latest_date = hist_df["run_date"].max()
today_trends = hist_df[hist_df["run_date"] == latest_date]
top_overall_phrase = today_trends.sort_values("relevance_score", ascending=False).iloc[0]["trend_phrase"]

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        f"<div class='metric-card'><h3>Active Database Date</h3><h2>{latest_date.strftime('%Y-%m-%d')}</h2></div>",
        unsafe_embed_allowed=True)
with col2:
    st.markdown(
        f"<div class='metric-card accent-card'><h3>Top Spiking Phrase</h3><h2>{top_overall_phrase.upper()}</h2></div>",
        unsafe_embed_allowed=True)
with col3:
    st.markdown(
        f"<div class='metric-card'><h3>Analyzed Creators</h3><h2>{vid_df['channel'].nunique():,} Channels</h2></div>",
        unsafe_embed_allowed=True)

st.write("---")

# --- CHARTING AREA ---
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Maximum Occurring Trend Matrix")
    st.caption("Volume bubble density chart mapping overall keyword tracking frequencies.")

    # Process frequency counts across historical data
    bubble_data = hist_df.groupby("trend_phrase").agg(
        occurrences=("trend_phrase", "count"),
        avg_relevance=("relevance_score", "mean")
    ).reset_index()

    fig_bubble = px.scatter(
        bubble_data, x="avg_relevance", y="occurrences", text="trend_phrase",
        size="occurrences", color="avg_relevance",
        color_continuous_scale=["#0B2341", "#E35205"],
        labels={"avg_relevance": "Average Relevance Weight", "occurrences": "Days Tracked Logged"}
    )
    fig_bubble.update_traces(textposition='top center')
    fig_bubble.update_layout(plot_bgcolor="white", paper_bgcolor="white", showlegend=False)
    st.plotly_chart(fig_bubble, use_container_width=True)

with col_right:
    st.subheader("Historical Timeline Trajectory")
    st.caption("Select tracked phrases to isolate their performance over time.")

    unique_phrases = sorted(hist_df["trend_phrase"].unique())
    selected_phrases = st.multiselect("Filter Tracked Key-phrases:", unique_phrases, default=unique_phrases[:3])

    if selected_phrases:
        timeline_df = hist_df[hist_df["trend_phrase"].isin(selected_phrases)].sort_values("run_date")
        fig_line = px.line(
            timeline_df, x="run_date", y="relevance_score", color="trend_phrase",
            color_discrete_sequence=["#0B2341", "#E35205", "#708090", "#4682B4"],
            labels={"run_date": "Timeline Run Date", "relevance_score": "Trending Value"}
        )
        fig_line.update_layout(plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Select phrases above to plot their timeline vector trajectory.")

st.write("---")

# --- CONTEXTUALLY INTERACTIVE VIDEO DRILLDOWN ---
st.subheader("Targeted Content Deep-Dive")
selected_trend = st.selectbox("Isolate Specific Phrase to Locate Source Videos:", unique_phrases)


# Text matcher helper function
def matches_trend(row, phrase):
    target_pool = f"{row.get('title', '')} {row.get('description', '')} {row.get('tags', '')}".lower()
    words = phrase.lower().split()
    return all(word in target_pool for word in words)


if selected_trend:
    # Filter videos containing all words of the selected keyphrase
    matched_mask = vid_df.apply(lambda row: matches_trend(row, selected_trend), axis=1)
    matched_vids = vid_df[matched_mask].sort_values("engagement_score", ascending=False)

    if not matched_vids.empty:
        st.write(f"Displaying **{len(matched_vids)}** video records matching the phrase: *\"{selected_trend}\"*")

        # Display as clear dashboard list
        for _, row in matched_vids.head(10).iterrows():
            with st.container():
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.markdown(f"**[{row['title']}]({row['video_link']})**")
                    st.caption(f"Channel: {row['channel']} | Published: {str(row['published_at'])[:10]}")
                with c2:
                    st.metric("Raw Views", f"{int(row['view_count']):,}")
                with c3:
                    st.metric("Engagement Metric", f"{int(row['engagement_score']):,}")
                st.markdown("<div style='border-bottom:1px solid #e2e8f0; margin-bottom:10px;'></div>",
                            unsafe_embed_allowed=True)
    else:
        st.info(
            "The selected historical phrase was identified across previous batch iterations, but matching videos are not in the current search snapshot.")