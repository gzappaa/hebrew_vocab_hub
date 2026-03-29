import re
import random
from pathlib import Path

# Base directory (vai de scripts/ -> data/)
BASE_DIR = Path(__file__).parent.parent

# Directory where individual .txt song files are stored
SONGS_DIR = BASE_DIR / "songs"

# Output file where all lyrics will be combined
OUTPUT_FILE = BASE_DIR / "all_lyrics.txt"

# Regex to remove artist names at the end of a line
artist_pattern = re.compile(r"\s*[-–]\s*[\w\s'״&]+$")

# Regex to remove anything inside brackets, even multiline
bracket_pattern = re.compile(r"\[.*?\]", re.DOTALL)

all_lines = []

for fpath in SONGS_DIR.glob("*.txt"):
    seen_lines = set()  # set for this music only
    with open(fpath, "r", encoding="utf-8") as f:
        text = f.read()
        text = text.replace("\u200e", "")  # remove invisible char U+200E
        text = bracket_pattern.sub("", text)  # remove everything in brackets
        lines = text.splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue  # skip empty lines
            line = artist_pattern.sub("", line)  # remove artist at end
            line = line.strip()
            if line and line not in seen_lines:
                all_lines.append(line)
                seen_lines.add(line)

# Shuffle all lines before writing
random.shuffle(all_lines)

with open(OUTPUT_FILE, "w", encoding="utf-8") as out_f:
    for line in all_lines:
        out_f.write(line + "\n")

print(f"All lyrics combined and shuffled in: {OUTPUT_FILE.name}")