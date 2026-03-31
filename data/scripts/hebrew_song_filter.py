import re
import json
from pathlib import Path
from bs4 import BeautifulSoup

# paths
BASE_DIR = Path(__file__).parent.parent  # from scripts/ -> data/
HTML_FILE = BASE_DIR / "Spotify_Weekly_Chart_Totals-Israel.html"
OUTPUT_FILE = BASE_DIR / "hebrew_songs.json"

# load the HTML
with open(HTML_FILE, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

# regex to match "Artist - Title" where Title has at least one Hebrew char
pattern = re.compile(r'^(.*?)\s*-\s*(.*[\u0590-\u05FF].*)$')

songs = []

for div in soup.select("td.text.mp div"):
    text = div.get_text(strip=True)
    m = pattern.match(text)
    if m:
        artist = m.group(1)
        title = m.group(2)
        songs.append({"artist": artist, "title": title})

# save to JSON
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(songs, f, ensure_ascii=False, indent=2)

print(f"{len(songs)} Hebrew songs saved to {OUTPUT_FILE.name}")