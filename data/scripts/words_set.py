import json
from pathlib import Path
import re
import unicodedata

# --- paths ---
root = Path(__file__).parent.parent
data_dir = root
data_dir.mkdir(exist_ok=True)  # ensures data directory exists

unique_words_file = data_dir / "unique_words.txt"
hebrew_words_file = data_dir / "hebrew_words.json"
output_file = data_dir / "common_words.json"

# --- regex to remove non-Hebrew characters ---
non_hebrew_re = re.compile(r'[^\u0590-\u05FF]')

# --- function to clean word: removes nekudot (vowel points) and non-Hebrew chars ---
def clean_word(word):
    # decompose Unicode and remove diacritics (nekudot)
    no_nekud = ''.join(
        c for c in unicodedata.normalize('NFD', word)
        if not unicodedata.combining(c)
    )
    # remove anything that is not Hebrew letters
    return non_hebrew_re.sub('', no_nekud)

# --- load unique_words.txt and clean ---
with open(unique_words_file, "r", encoding="utf-8") as f:
    unique_words_set = set(
        clean_word(line.strip())
        for line in f
        if line.strip()
    )

# --- load hebrew_words.json and clean ---
with open(hebrew_words_file, "r", encoding="utf-8") as f:
    hebrew_words_list = json.load(f)

hebrew_words_set = set(clean_word(word) for word in hebrew_words_list)

# --- intersection of both sets ---
common_words = sorted(unique_words_set & hebrew_words_set)

# --- save result to JSON in data folder ---
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(common_words, f, ensure_ascii=False, indent=2)

print(f"Total words in both sources after cleaning: {len(common_words)}")
print(f"Saved to: {output_file}")