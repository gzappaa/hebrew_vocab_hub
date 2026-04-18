import json
from pathlib import Path
import re

# -----------------------------
# Paths
# -----------------------------
root = Path(__file__).parent.parent
data_dir = root
data_dir.mkdir(exist_ok=True)

lyrics_file = root / "all_lyrics.txt"
articles_file = root / "hadshon_articles.json"
trending_file = root / "trending_23-03-2026.json"
output_file = data_dir / "unique_words.txt"

# -----------------------------
# Regex: match Hebrew words
# -----------------------------
hebrew_re = re.compile(r'[\u0590-\u05FF]+')

# -----------------------------
# Store unique words
# -----------------------------
unique_words = set()

# -----------------------------
# Part 1: Lyrics
# -----------------------------
with open(lyrics_file, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        words = hebrew_re.findall(line)
        unique_words.update(words)

# -----------------------------
# Part 2: Articles
# -----------------------------
with open(articles_file, "r", encoding="utf-8") as f:
    articles = json.load(f)
    for item in articles:
        text = item.get("title", "") + " " + item.get("text", "")
        words = hebrew_re.findall(text)
        unique_words.update(words)

# -----------------------------
# Part 3: Trending comments
# -----------------------------
with open(trending_file, "r", encoding="utf-8") as f:
    videos = json.load(f)
    for video in videos:
        for comment in video.get("comments", []):
            text = comment.get("text", "")
            words = hebrew_re.findall(text)
            unique_words.update(words)

# -----------------------------
# Save result
# -----------------------------
unique_words_list = sorted(unique_words)

with open(output_file, "w", encoding="utf-8") as f:
    for word in unique_words_list:
        f.write(word + "\n")

print(f"Total unique Hebrew words from all sources: {len(unique_words_list)}")
print(f"Saved to: {output_file}")