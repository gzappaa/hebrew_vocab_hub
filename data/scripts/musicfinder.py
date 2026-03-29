import json
import requests
import time
from pathlib import Path
import os
from dotenv import load_dotenv

# -----------------------------
# Load environment variables
# -----------------------------
ROOT_DIR = Path(__file__).parent.parent.parent  # scripts/ -> data/ -> project root
load_dotenv(ROOT_DIR / ".env")

ACCESS_TOKEN = os.getenv("CLIENT_ACCESS_TOKEN")
if not ACCESS_TOKEN:
    raise ValueError("CLIENT_ACCESS_TOKEN not found in .env")

# -----------------------------
# Configuration
# -----------------------------
BASE_DIR = Path(__file__).parent.parent  # scripts/ -> data/
INPUT_JSON = BASE_DIR / "hebrew_songs.json"  # input JSON with songs
OUTPUT_JSON = BASE_DIR / "hebrew_songs_genius.json"  # output JSON with URLs
LOG_FILE = BASE_DIR / "hebrew_songs_log.txt"  # log file
MAX_SONGS = 500  # stop after finding 500 songs
SLEEP_BETWEEN_REQUESTS = 0.5  # pause to avoid API limits

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

# -----------------------------
# Load input songs
# -----------------------------
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    songs = json.load(f)

found_songs = []
errors = 0

# -----------------------------
# Loop through songs and search on Genius
# -----------------------------
with open(LOG_FILE, "w", encoding="utf-8") as log_file:
    for idx, song in enumerate(songs, start=1):
        artist = song.get("artist")
        title = song.get("title")
        query = f"{title} {artist}"

        try:
            res = requests.get(
                "https://api.genius.com/search",
                headers=HEADERS,
                params={"q": query}
            )

            # Check HTTP status
            if res.status_code != 200:
                log_file.write(f"[{idx}] ERROR HTTP {res.status_code}: {artist} - {title}\n")
                errors += 1
                continue

            data = res.json()
            hits = data.get("response", {}).get("hits", [])

            if not hits:
                log_file.write(f"[{idx}] NOT FOUND: {artist} - {title}\n")
                errors += 1
                continue

            # Take the first hit
            result = hits[0]["result"]
            song_url = "https://genius.com" + result.get("path", "")

            found_songs.append({
                "artist": artist,
                "title": title,
                "url": song_url
            })

            log_file.write(f"[{idx}] FOUND: {artist} - {title} -> {song_url}\n")
            print(f"[{len(found_songs)}] FOUND: {artist} - {title} -> {song_url}")

            # Stop if MAX_SONGS reached
            if len(found_songs) >= MAX_SONGS:
                log_file.write(f"\nReached {MAX_SONGS} songs. Stopping.\n")
                break

        except Exception as e:
            log_file.write(f"[{idx}] EXCEPTION: {artist} - {title} -> {e}\n")
            errors += 1

        time.sleep(SLEEP_BETWEEN_REQUESTS)

# -----------------------------
# Save final JSON
# -----------------------------
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(found_songs, f, ensure_ascii=False, indent=2)

# -----------------------------
# Summary
# -----------------------------
print(f"\nFinished. Total found: {len(found_songs)} / Errors: {errors}")