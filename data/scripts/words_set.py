import json
from pathlib import Path
import re
import unicodedata

# --- paths ---
root = Path(__file__).parent.parent
data_dir = root
data_dir.mkdir(exist_ok=True)

unique_words_file = data_dir / "unique_words.txt"
hebrew_words_file = data_dir / "hebrew_words_RAW.json"
output_file = data_dir / "common_words.json"

# --- regex to keep only Hebrew letters ---
non_hebrew_re = re.compile(r'[^\u0590-\u05FF]')


# --- clean function ---
def clean_word(word: str):
    if not word:
        return None

    # remove nekudot (vowel points)
    no_nekud = ''.join(
        c for c in unicodedata.normalize('NFD', word)
        if not unicodedata.combining(c)
    )

    # keep only Hebrew letters
    cleaned = non_hebrew_re.sub('', no_nekud)

    # IMPORTANT: drop empty results
    return cleaned if cleaned else None


# --- load + clean unique_words.txt ---
unique_words_set = set()

with open(unique_words_file, "r", encoding="utf-8") as f:
    for line in f:
        cw = clean_word(line.strip())
        if cw:
            unique_words_set.add(cw)


# --- load + clean hebrew_words.json ---
with open(hebrew_words_file, "r", encoding="utf-8") as f:
    hebrew_words_list = json.load(f)

hebrew_words_set = set()

for word in hebrew_words_list:
    cw = clean_word(word)
    if cw:
        hebrew_words_set.add(cw)


# --- intersection ---
common_words = sorted(unique_words_set & hebrew_words_set)


# --- save result ---
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(common_words, f, ensure_ascii=False, indent=2)


print(f"Total words in both sources: {len(common_words)}")
print(f"Saved to: {output_file}")