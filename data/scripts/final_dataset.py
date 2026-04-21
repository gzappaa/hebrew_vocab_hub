"""
build_vocab_dataset.py 

Matching logic:
  For every entry in dict-complete.json, collect ALL Hebrew forms that appear:
    - entry["hebrew"]  (base form)
    - every cell["hebrew"] inside every table row
  Strip niqqudot from each form. If ANY of them matches the common_words word
  (also stripped), that dict entry counts as a meaning of that word.

This means:
  - חברה (bare) matches חֶבְרָה (chevra / company)        ✓
  - חברה (bare) matches חֲבֵרָה (chavera / girlfriend)     ✓
  - חברה (bare) matches חִבְּרָה (hi'bra / she connected)  ✓  ← verb past 3fs
  - חברתכן (bare) does NOT match חברה                      ✓  (different bare form)

Output schema per entry:
{
  "word": "חברה",
  "multiple_meanings": true,
  "meanings": [
    {
      "hebrew": "חֶבְרָה",
      "transcription": "chevra",
      "root": "ח - ב - ר",
      "part_of_speech": "...",
      "meaning": "company, society",
      "audio_url": "...",
      "word_url": "...",
      "tables": [...]
    },
    ...
  ],
  "sentences": [
    { "sentence": "...", "translation": "...", "source": "tatoeba" }
  ]
}
"""

import json
import re
from pathlib import Path
from collections import defaultdict

# ── Paths ──────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent.parent.parent
COMMON_WORDS_PATH = BASE / "data" / "common_words.json"
DICT_PATH         = BASE / "dict-complete.json"
SENTENCES_REVERSO = BASE / "data" / "sentences_reverso.json"
SENTENCES_TATOEBA = BASE / "data" / "sentences_tatoeba.json"
WORD_SOURCES_PATH = BASE / "data" / "word_sources.json"
OUTPUT_PATH       = BASE / "data" / "vocab_dataset.json"


# ── Niqqud stripping ───────────────────────────────────────────────────────
# Must match exactly the clean_word() logic used to build common_words.json:
#   unicodedata.normalize('NFD') → decomposes chars into base + combining
#   filter out combining chars (niqqudot decompose to combining codepoints)
#   keep only Hebrew letters U+05D0–U+05EA (what non_hebrew_re keeps)
import unicodedata as _ud

KEEP_HEBREW_RE = re.compile(r'[^\u05D0-\u05EA]')

def strip_niqqud(text: str) -> str:
    # Step 1: NFD decompose so niqqudot become separate combining chars
    decomposed = _ud.normalize('NFD', text)
    # Step 2: drop all combining characters (niqqudot, cantillation marks)
    no_combining = ''.join(c for c in decomposed if not _ud.combining(c))
    # Step 3: keep only Hebrew base letters (same as non_hebrew_re in clean_word)
    hebrew_only = KEEP_HEBREW_RE.sub('', no_combining)
    return hebrew_only.strip()


# ── Helpers ────────────────────────────────────────────────────────────────
def load_json(path: Path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def extract_word_string(entry) -> str:
    if isinstance(entry, str):
        return entry.strip()
    if isinstance(entry, dict):
        for key in ("word", "hebrew", "text"):
            if key in entry:
                return str(entry[key]).strip()
    raise ValueError(f"Cannot extract word from entry: {entry!r}")


def all_hebrew_forms(dict_entry: dict) -> set:
    """
    Collect every bare (no-niqqud) Hebrew string that appears in a dict entry:
      - top-level "hebrew" field (base/citation form)
      - every cell["hebrew"] in every table (all inflections)
    """
    forms = set()

    base = dict_entry.get("hebrew", "")
    if base:
        forms.add(strip_niqqud(base))

    for table in dict_entry.get("tables", []):
        for row in table.get("rows", []):
            for cell in row.get("cells", []):
                h = cell.get("hebrew", "")
                if h:
                    bare = strip_niqqud(h)
                    # strip maqaf used in construct state: חַבְרַת־
                    bare = bare.rstrip('\u05be').rstrip('-').strip()
                    if bare:
                        forms.add(bare)

    return forms


# ── Load data ──────────────────────────────────────────────────────────────
print("Loading files...")
common_words_raw = load_json(COMMON_WORDS_PATH)
dict_entries     = load_json(DICT_PATH)
sentences_rev    = load_json(SENTENCES_REVERSO)
sentences_tat    = load_json(SENTENCES_TATOEBA)
word_sources_raw = load_json(WORD_SOURCES_PATH)

print(f"  common_words : {len(common_words_raw):,}")
print(f"  dict entries : {len(dict_entries):,}")
print(f"  sentences rev: {len(sentences_rev):,}")
print(f"  sentences tat: {len(sentences_tat):,}")
print(f"  word_sources : {len(word_sources_raw):,}")


# ── Index: bare form → list of dict entries that contain that form ─────────
print("Indexing dict forms...")
form_to_entries = defaultdict(list)

for entry in dict_entries:
    for bare_form in all_hebrew_forms(entry):
        form_to_entries[bare_form].append(entry)

print(f"  Unique bare forms indexed: {len(form_to_entries):,}")


# ── Sentence lookup ────────────────────────────────────────────────────────
def build_sentence_lookup(sentences, source_name):
    lookup = defaultdict(list)
    for s in sentences:
        bare = strip_niqqud(s.get("word", ""))
        if bare:
            lookup[bare].append({
                "sentence":    s.get("sentence", ""),
                "translation": s.get("translation", ""),
                "source":      source_name,
            })
    return lookup

sent_rev = build_sentence_lookup(sentences_rev, "reverso")
sent_tat = build_sentence_lookup(sentences_tat, "tatoeba")

def get_sentences(bare_word):
    combined = sent_rev.get(bare_word, []) + sent_tat.get(bare_word, [])
    seen, unique = set(), []
    for s in combined:
        key = s["sentence"].strip()
        if key not in seen:
            seen.add(key)
            unique.append(s)
    return unique


# ── Word sources lookup ───────────────────────────────────────────────────
sources_lookup = {}
for s in word_sources_raw:
    bare = strip_niqqud(s.get("word", ""))
    if bare:
        sources_lookup[bare] = {
            "songs":   s.get("songs", 0),
            "news":    s.get("news", 0),
            "youtube": s.get("youtube", 0),
            "total":   s.get("total", 0),
        }

# ── Build dataset ──────────────────────────────────────────────────────────
print("Building dataset...")
dataset = []
not_found = []

for raw_entry in common_words_raw:
    word = extract_word_string(raw_entry)
    bare = strip_niqqud(word)

    matched_entries = form_to_entries.get(bare, [])

    # Deduplicate: same dict entry can be indexed under multiple bare forms
    seen_ids = set()
    unique_meanings = []
    for m in matched_entries:
        uid = m.get("word_url") or m.get("hebrew", "")
        if uid not in seen_ids:
            seen_ids.add(uid)
            unique_meanings.append(m)

    sentences = get_sentences(bare)

    dataset.append({
        "word":              bare,
        "multiple_meanings": len(unique_meanings) > 1,
        "meanings":          unique_meanings,
        "sentences":         sentences,
        "sources":           sources_lookup.get(bare, {}),
    })

    if not unique_meanings:
        not_found.append(bare)


# ── Write output ───────────────────────────────────────────────────────────
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(dataset, f, ensure_ascii=False, indent=2)

multi     = sum(1 for e in dataset if e["multiple_meanings"])
with_sent = sum(1 for e in dataset if e["sentences"])

print(f"\nDone! → {OUTPUT_PATH}")
print(f"  Total entries       : {len(dataset):,}")
print(f"  multiple_meanings   : {multi:,}")
print(f"  With sentences      : {with_sent:,}")
print(f"  Not found in dict   : {len(not_found):,}")
if not_found:
    print(f"  Not-found sample    : {not_found[:20]}")