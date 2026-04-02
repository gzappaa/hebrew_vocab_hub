import requests
import json
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
import os
import re

# -----------------------------
# Paths
# -----------------------------
SCRIPT_DIR = Path(__file__).parent             
ROOT_DIR = SCRIPT_DIR.parent.parent          
DATA_DIR = ROOT_DIR / "data"               
JSON_FILE = DATA_DIR / "trending_daily.json"  

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv(ROOT_DIR / ".env")
API_KEY_YOUTUBE = os.getenv("API_KEY_YOUTUBE")
BASE = "https://www.googleapis.com/youtube/v3"

HEBREW_REGEX = re.compile(r"[\u0590-\u05FF]")


class QuotaExceededException(Exception):
    pass


def get_trending_videos(region="IL", max_results=50):
    url = f"{BASE}/videos"
    params = {
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": region,
        "maxResults": max_results,
        "key": API_KEY_YOUTUBE,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get("items", [])


def filter_hebrew_videos(videos):
    return [
        v for v in videos
        if HEBREW_REGEX.search(v["snippet"]["title"]) or
           HEBREW_REGEX.search(v["snippet"]["channelTitle"])
    ]


def get_comments(video_id, existing_ids=None):
    url = f"{BASE}/commentThreads"
    comments = []
    page_token = None
    existing_ids = existing_ids or set()

    while True:
        params = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": 100,
            "order": "relevance",
            "key": API_KEY_YOUTUBE,
        }
        if page_token:
            params["pageToken"] = page_token

        response = requests.get(url, params=params)

        if response.status_code == 403:
            reason = response.json().get("error", {}).get("errors", [{}])[0].get("reason", "")
            if reason == "quotaExceeded":
                raise QuotaExceededException()
            return comments

        response.raise_for_status()
        data = response.json()

        for c in data.get("items", []):
            comment_id = c["snippet"]["topLevelComment"]["id"]
            if comment_id in existing_ids:
                continue
            top = c["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "id": comment_id,
                "author": top["authorDisplayName"],
                "text": top["textDisplay"],
                "likes": top["likeCount"],
                "published_at": top["publishedAt"][:10],
            })
            existing_ids.add(comment_id)

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    return comments


def load_existing():
    if JSON_FILE.exists():
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            return {v["video_id"]: v for v in json.load(f)}
    return {}


def save(data_dict):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(list(data_dict.values()), f, ensure_ascii=False, indent=2)


def main():
    print("Fetching trending videos in Israel...\n")
    videos = filter_hebrew_videos(get_trending_videos(max_results=50))
    print(f"Hebrew videos found: {len(videos)}\n")

    if not videos:
        print("No Hebrew videos found today.")
        return

    existing_data = load_existing()
    total_new = 0
    quota_exceeded = False

    for video in videos:
        if quota_exceeded:
            break

        video_id = video["id"]
        snippet = video["snippet"]
        stats = video["statistics"]
        title = snippet["title"]

        if video_id in existing_data:
            entry = existing_data[video_id]
            existing_ids = set(c["id"] for c in entry.get("comments", []) if "id" in c)
            print(f"Known: {title[:60]} | Comments: {len(existing_ids)}")
        else:
            entry = {
                "video_id": video_id,
                "title": title,
                "channel": snippet["channelTitle"],
                "published_at": snippet["publishedAt"][:10],
                "views": stats.get("viewCount", "0"),
                "likes": stats.get("likeCount", "0"),
                "comment_count": stats.get("commentCount", "0"),
                "first_seen": datetime.now().strftime("%Y-%m-%d"),
                "last_seen": datetime.now().strftime("%Y-%m-%d"),
                "comments": [],
            }
            existing_ids = set()
            print(f"New:   {title[:60]}")

        entry["views"] = stats.get("viewCount", "0")
        entry["likes"] = stats.get("likeCount", "0")
        entry["last_seen"] = datetime.now().strftime("%Y-%m-%d")

        try:
            new_comments = get_comments(video_id, existing_ids=existing_ids)
            entry["comments"].extend(new_comments)
            total_new += len(new_comments)
            print(f"  +{len(new_comments)} comments | Total: {len(entry['comments'])}")

        except QuotaExceededException:
            quota_exceeded = True
            existing_data[video_id] = entry
            save(existing_data)
            print("\n" + "=" * 60)
            print("🚫  QUOTA EXCEEDED")
            print(f"    Saved — {total_new} new comments today.")
            print("=" * 60)
            return

        existing_data[video_id] = entry
        save(existing_data)

    print("\n" + "=" * 60)
    print("✅  DONE")
    print(f"    {total_new} new comments | {len(existing_data)} videos tracked")
    print("=" * 60)


if __name__ == "__main__":
    main()