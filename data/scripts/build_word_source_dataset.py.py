import json
from pathlib import Path
import re
from collections import defaultdict

# -----------------------------
# Paths
# -----------------------------
root = Path(__file__).parent.parent

lyrics_file = root / "all_lyrics.txt"
news_file = root / "hadshon_articles.json"
youtube_file = root / "trending_23-03-2026.json"

output_file = root / "word_sources.json"

# -----------------------------
# Regex: Hebrew words
# -----------------------------
hebrew_re = re.compile(r'[\u0590-\u05FF]+')

# -----------------------------
# Data structure
# -----------------------------
data = defaultdict(lambda: {
    "songs": 0,
    "news": 0,
    "youtube": 0
})

# -----------------------------
# Part 1: Songs
# -----------------------------
with open(lyrics_file, "r", encoding="utf-8") as f:
    for line in f:
        words = hebrew_re.findall(line)
        for w in words:
            data[w]["songs"] += 1

# -----------------------------
# Part 2: News
# -----------------------------
with open(news_file, "r", encoding="utf-8") as f:
    articles = json.load(f)
    for item in articles:
        text = item.get("title", "") + " " + item.get("text", "")
        words = hebrew_re.findall(text)
        for w in words:
            data[w]["news"] += 1

# -----------------------------
# Part 3: YouTube
# -----------------------------
with open(youtube_file, "r", encoding="utf-8") as f:
    videos = json.load(f)
    for video in videos:
        for comment in video.get("comments", []):
            text = comment.get("text", "")
            words = hebrew_re.findall(text)
            for w in words:
                data[w]["youtube"] += 1

# -----------------------------
# Convert to list format
# -----------------------------
final_data = []

for word, sources in data.items():
    total = sources["songs"] + sources["news"] + sources["youtube"]

    if total > 0:
        final_data.append({
            "word": word,
            "songs": sources["songs"],
            "news": sources["news"],
            "youtube": sources["youtube"],
            "total": total
        })

# -----------------------------
# Save
# -----------------------------
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(final_data, f, ensure_ascii=False, indent=2)

print(f"Total words: {len(final_data)}")
print(f"Saved to: {output_file}")