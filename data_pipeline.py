import os
import re
import json
import pandas as pd
import yake
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2 import service_account

load_dotenv()

# --- SECURITY HANDSHAKE CONFIGURATION ---
API_KEY = os.getenv("YOUTUBE_API_KEY")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS")

# Target Google Sheet Name (Must match exactly what you named your file)
#SPREADSHEET_NAME = "MakerTrends_Database"
SPREADSHEET_ID = "1MtzB35dorD9YUHLlVzfratj27gcdmn2XTZLoVzCIl68"
# Authenticate both APIs
youtube = build("youtube", "v3", developerKey=API_KEY)

if not GOOGLE_CREDS_JSON:
    raise ValueError("CRITICAL: GOOGLE_CREDS secret environment variable is missing!")

creds_dict = json.loads(GOOGLE_CREDS_JSON)
google_scopes = ["https://www.googleapis.com/auth/spreadsheets"]
sheets_creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=google_scopes)
sheets_service = build("sheets", "v4", credentials=sheets_creds)

SEARCH_TERMS = [
    "power tools latest use cases", "cordless drill projects", "impact driver uses",
    "angle grinder projects", "oscillating multi tool uses", "rotary hammer drill uses",
    "DIY power tools trends", "construction power tool hacks", "woodworking power tools projects",
    "furniture flip", "thrift flip", "dresser makeover", "cabinet makeover",
    "furniture restoration", "tool restoration", "restoration projects",
    "restoration hacks", "carving project ideas"
]

DAYS_BACK = 90
MAX_RESULTS_PER_QUERY = 25

def search_videos(query):
    published_after = (datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)).isoformat()
    try:
        request = youtube.search().list(
            part="snippet", q=query, type="video", order="relevance",
            publishedAfter=published_after, maxResults=MAX_RESULTS_PER_QUERY,
            relevanceLanguage="en", regionCode="GB", safeSearch="moderate"
        )
        response = request.execute()
    except Exception as e:
        print(f"API Error searching for {query}: {e}")
        return []

    rows = []
    channel_ids = []
    for item in response.get("items", []):
        video_id = item["id"].get("videoId")
        if not video_id:
            continue
        channel_id = item["snippet"]["channelId"]
        channel_ids.append(channel_id)

        rows.append({
            "video_id": video_id,
            "video_link": f"https://www.youtube.com/watch?v={video_id}",
            "channel_id": channel_id,
            "query": query,
            "title": item["snippet"]["title"],
            "description": item["snippet"]["description"],
            "channel": item["snippet"]["channelTitle"],
            "published_at": item["snippet"]["publishedAt"],
        })

    if channel_ids:
        try:
            channel_response = youtube.channels().list(part="statistics", id=",".join(set(channel_ids))).execute()
            channel_stats = {item["id"]: int(item["statistics"].get("subscriberCount", 0)) for item in channel_response.get("items", [])}
            for row in rows:
                row["subscriber_count"] = channel_stats.get(row["channel_id"], 0)
        except Exception as e:
            print(f"API Error fetching channel stats: {e}")
            for row in rows:
                row["subscriber_count"] = 0
    return rows

def get_video_stats(video_ids):
    if not video_ids:
        return []
    rows = []
    try:
        request = youtube.videos().list(part="snippet,statistics", id=",".join(video_ids))
        response = request.execute()
        for item in response.get("items", []):
            stats = item.get("statistics", {})
            snippet = item.get("snippet", {})
            rows.append({
                "video_id": item["id"],
                "tags": ", ".join(snippet.get("tags", [])) if snippet.get("tags") else "",
                "view_count": int(stats.get("viewCount", 0)),
                "like_count": int(stats.get("likeCount", 0)),
                "comment_count": int(stats.get("commentCount", 0)),
            })
    except Exception as e:
        print(f"API Error fetching video stats: {e}")
    return rows

def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"\b(tools|diy)\b", " ", text)
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def extract_trends(df, top_n=25):
    full_text = " ".join((df["title"].fillna("") + " " + df["description"].fillna("") + " " + df["tags"].fillna("")).map(clean_text))
    kw_extractor = yake.KeywordExtractor(lan="en", n=2, dedupLim=0.9, top=top_n * 4, features=None)
    keywords = kw_extractor.extract_keywords(full_text)
    two_word_keywords = [kw for kw in keywords if len(kw[0].split()) == 2]
    trend_df = pd.DataFrame(two_word_keywords, columns=["trend_phrase", "yake_score"]).sort_values("yake_score", ascending=True)
    return trend_df.head(top_n)



def export_to_google_sheet(spreadsheet_id, range_name, df, mode="overwrite"):
    # Clear and overwrite or append raw dataframe matrix to targeted tabs
    data_payload = [df.columns.tolist()] + df.astype(str).values.tolist()
    
    if mode == "overwrite":
        sheets_service.spreadsheets().values().clear(spreadsheetId=spreadsheet_id, range=range_name).execute()
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption="USER_ENTERED", body={"values": data_payload}
        ).execute()
    elif mode == "append":
        # Check if tab has content. If it does, omit sending the header row
        existing = sheets_service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        payload = data_payload if not existing.get("values") else data_payload[1:]
        if payload:
            sheets_service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id, range=range_name,
                valueInputOption="USER_ENTERED", body={"values": payload}
            ).execute()

def main():
    print("Starting collection pipeline...")
    all_rows = []
    for query in SEARCH_TERMS:
        all_rows.extend(search_videos(query))

    if not all_rows:
        print("Empty extraction pool.")
        return

    df = pd.DataFrame(all_rows).drop_duplicates("video_id")
    video_ids = df["video_id"].tolist()
    
    stats = []
    for i in range(0, len(video_ids), 50):
        stats.extend(get_video_stats(video_ids[i:i + 50]))

    stats_df = pd.DataFrame(stats)
    if not stats_df.empty:
        df = df.merge(stats_df, on="video_id", how="left")
        
    df["engagement_score"] = df["view_count"].fillna(0) + (df["like_count"].fillna(0) * 10) + (df["comment_count"].fillna(0) * 20)
    df = df.sort_values("engagement_score", ascending=False)

    trends = extract_trends(df)
    run_date = datetime.now().strftime("%Y-%m-%d")
    trends.insert(0, "run_date", run_date)

    # Push to Google Cloud Sheets
    try:
        # Save video snapshot to Sheet tab 'Latest_Videos' (overwrites daily)
        print("Syncing video inventory dataset...")
        export_to_google_sheet(SPREADSHEET_ID, "Latest_Videos!A1", df, mode="overwrite")
        
        # Append today's trending phrases into Sheet tab 'Trends_History'
        print("Syncing phrase trend history database...")
        export_to_google_sheet(SPREADSHEET_ID, "Trends_History!A1", trends, mode="append")
        
        print("Data streams cleanly synced with Google Sheets!")
    except Exception as e:
        print(f"Google Cloud Sheet Pipeline Sync Failed: {e}")

if __name__ == "__main__":
    main()
