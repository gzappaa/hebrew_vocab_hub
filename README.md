# hebrew_vocab_hub

A data pipeline that builds a structured Hebrew vocabulary dataset from multiple real-world sources — dictionary entries, song lyrics, news articles, YouTube comments, and bilingual sentence corpora — and outputs a single unified JSON ready for use in language learning APIs, apps, or databases.

Built with **Scrapy** for web scraping, **Playwright** for browser automation against private APIs, **pandas** for data export, **MySQL** and **MongoDB** as intermediate storage during scraping, and **Python** scripts for all data processing and assembly. The scraping layer stores data in parallel to SQL, MongoDB, and Excel during development; the final pipeline works entirely from JSON files on disk.

---

## What it produces

`data/vocab_dataset.json` — ~13,000 Hebrew words (unvocalized), each entry containing:

```json
{
  "word": "חברה",
  "multiple_meanings": true,
  "meanings": [
    {
      "hebrew": "חֶבְרָה",
      "transcription": "chevra",
      "root": "ח - ב - ר",
      "part_of_speech": "Noun - feminine",
      "meaning": "company, society",
      "audio_url": "https://audio.pealim.com/...",
      "word_url": "https://www.pealim.com/dict/...",
      "tables": [...]
    },
    {
      "hebrew": "חֲבֵרָה",
      "transcription": "chavera",
      "meaning": "girlfriend; female friend; member",
      ...
    }
  ],
  "sentences": [
    { "sentence": "היא חברה שלי.", "translation": "She is my friend.", "source": "tatoeba" },
    { "sentence": "החברה הזו גדולה.", "translation": "This company is big.", "source": "reverso" }
  ],
  "sources": {
    "songs": 12,
    "news": 45,
    "youtube": 8,
    "total": 65
  }
}
```

`multiple_meanings: true` is set whenever the same unvocalized spelling (e.g. חברה) maps to two or more distinct dictionary entries — different words that are only distinguishable by their niqqudot (vowel points).

Hebrew is normally written without niqqudot (vowel points) in modern text, so the same string can represent completely different words depending on context. חברה for example can be חֶבְרָה (company), חֲבֵרָה (girlfriend), or חִבְּרָה (she connected — past tense 3fs of לחבר). Matching is done across all inflected forms in the conjugation tables using Unicode NFD decomposition to strip combining characters, so any form that reduces to the same bare string gets grouped under the same entry. The `sources` field reflects how often that word appears in real Israeli content — songs, news, and YouTube comments — giving a rough measure of practical frequency.

The dataset is **PostgreSQL JSONB-ready** — insert the whole document into a `jsonb` column and index on `word`.

---

## Pipeline overview

```
pealim.com ──► spider_dict ──► dict.json
                                    │
                    spider_words ◄──┘
                          │
                          ▼
                  dict-complete.json ──► words.py ──► hebrew_words_RAW.json
                                                              │
Spotify charts ──► hebrew_song_filter ──► hebrew_songs.json  │
                          │                                   │
               musicfinder (Genius API)                       │
                          │                                   │
               spider_lyrics ──► songs/ ──► lyrics_scrambler ──► all_lyrics.txt
                                                              │
hadshon.gov.il ──► spider_hadshon ──► hadshon.json           │
               ──► spider_hadshon_articles ──► hadshon_articles.json
                                                              │
YouTube Data API ──► youtube_comments_daily ──► trending_daily.json
                                                              │
                    build_word_source_dataset ◄───────────────┤
                          │                         (songs + news + youtube)
                          ▼
                    word_sources.json
                                                              │
                    words_set.py ◄────────────────────────────┘
                    (unique_words.txt ∩ hebrew_words_RAW)
                          │
                          ▼
                    common_words.json (~13k words)
                          │
              ┌───────────┴────────────┐
              ▼                        ▼
    tatoeba_sentences.py      more_sentences.py
    (public API, ~10k)        (Playwright + Reverso, ~3k missing)
              │                        │
              └───────────┬────────────┘
                          ▼
              sentences_tatoeba.json + sentences_reverso.json
                          │
                          ▼
                    final_dataset.py
                          │
                          ▼
                    vocab_dataset.json ✓
```

---

## Project structure

```
hebrew_vocab_hub/
├── scraping/
│   ├── spiders/
│   │   ├── spider_dict.py          # Scrapes pealim.com/words page by page
│   │   ├── spider_words.py         # Visits each word URL, extracts all conjugation tables
│   │   ├── spider_hadshon.py       # Scrapes hadshon.co.il (gov vocabulary site for students) — collected, reserved for future use
│   │   ├── spider_hadshon_articles.py  # Scrapes hadshon news articles
│   │   └── spider_lyrics.py        # Scrapes lyrics from Genius URLs
│   ├── items.py
│   ├── pipelines.py            # SQLPipeline (MySQL), ExcelPipeline, MongoPipeline, WordsPipeline (MongoDB)
│   ├── middlewares.py
│   └── settings.py
│
├── data/
│   ├── scripts/
│   │   ├── words.py                # Extracts all Hebrew forms from dict-complete → hebrew_words_RAW.json
│   │   ├── words_set.py            # Intersects unique_words.txt ∩ hebrew_words_RAW → common_words.json
│   │   ├── hebrew_song_filter.py   # Filters Spotify Israel top 2000 for Hebrew-titled songs
│   │   ├── musicfinder.py          # Fetches Genius URLs for each Hebrew song
│   │   ├── lyrics_scrambler.py     # Merges all song txts, shuffles line order → all_lyrics.txt
│   │   ├── build_word_source_dataset.py  # Counts word frequency across songs/news/youtube
│   │   ├── tatoeba_sentences.py    # Fetches 3 example sentences per word from Tatoeba API
│   │   ├── state.py                # Generates Playwright auth state for Reverso
│   │   ├── more_sentences.py       # Fetches sentences for missing words via Reverso (Playwright)
│   │   ├── youtube_comments_daily.py  # Pulls top YouTube IL comments → trending_daily.json
│   │   └── final_dataset.py        # Assembles the final vocab_dataset.json
│   │
│   ├── common_words.json           # ~13k unvocalized Hebrew words
│   ├── dict-complete.json          # Full dictionary with niqqudot + conjugation tables
│   ├── word_sources.json           # Word frequency by source (songs / news / youtube)
│   ├── sentences_tatoeba.json      # Example sentences from Tatoeba
│   ├── sentences_reverso.json      # Example sentences from Reverso
│   ├── vocab_dataset.json          # ✓ Final unified dataset
│   └── ...
│
├── tests/                          # Unit tests for spiders and pipeline
├── .github/workflows/scraping.yaml # Runs pytest on every push and pull request
├── Makefile                        # Orchestrates the full pipeline
├── requirements.txt
└── .env
```

---

## Setup

**Requirements:** Python 3.10+, pip

```bash
git clone https://github.com/gzappaa/hebrew_vocab_hub
cd hebrew_vocab_hub
pip install -r requirements.txt
playwright install chromium
```

Create a `.env` file at the root:

```env
# MySQL (used by spider_dict pipeline)
MYSQL_HOST=
MYSQL_PORT=
MYSQL_USER=
MYSQL_PASSWORD=
MYSQL_DB=

# MongoDB (used by spider_dict and spider_words pipelines)
MONGO_URI=

# Genius API (used by musicfinder.py)
CLIENT_ID_GENIUS=
CLIENT_SECRET_GENIUS=
CLIENT_ACCESS_TOKEN=

# YouTube Data API v3 (used by youtube_comments_daily.py)
API_KEY_YOUTUBE=
```

> MySQL and MongoDB are only required if you want to use those scraping pipelines directly. The final dataset build (`make dataset`) only needs the JSON files on disk.

---

## Running the pipeline

### Full bootstrap (run once)

Runs everything from scratch except the daily YouTube trending step. Requires the Genius and YouTube API keys in `.env`.

```bash
make bootstrap
```

### Daily refresh

Fetches today's YouTube trending comments, rebuilds word frequency counts, and regenerates the final dataset.

```bash
make daily
```

### Individual steps

```bash
make scrape-dict            # Scrape pealim.com dictionary
make scrape-words           # Scrape conjugation tables for each word
make words-raw              # Extract all Hebrew forms → hebrew_words_RAW.json
make scrape-hadshon         # Scrape hadshon vocabulary site
make scrape-hadshon-articles  # Scrape hadshon news
make filter-songs           # Filter Spotify charts for Hebrew songs
make fetch-genius           # Fetch Genius lyric URLs
make scrape-lyrics          # Scrape and merge lyrics
make words-set              # Build common_words.json
make sentences              # Fetch example sentences (Tatoeba + Reverso)
make word-sources           # Build word frequency dataset
make dataset                # Build final vocab_dataset.json
make trending               # Fetch today's YouTube comments (daily only)
```

### Tests

```bash
make test                   # All tests
make test-spiders           # Spider tests only
make test-pipeline          # Pipeline tests only
```

---

## Data sources

| Source | What it provides | Script |
|--------|-----------------|--------|
| [pealim.com](https://www.pealim.com) | Dictionary entries with niqqudot, transcription, conjugation tables | `spider_dict`, `spider_words` |
| [hadshon.co.il](https://www.hadshon.co.il) | News articles used in word frequency counts (`hadshon_articles`). Vocabulary/abbreviations data (`hadshon`) collected and reserved for future use | `spider_hadshon`, `spider_hadshon_articles` |
| Spotify Israel top charts | Top ~2000 songs in Israel since 2018, filtered for Hebrew titles | `hebrew_song_filter` |
| [Genius](https://genius.com) | Song lyrics for each Hebrew track | `musicfinder`, `spider_lyrics` |
| [Tatoeba](https://tatoeba.org) | Bilingual example sentences (public API) | `tatoeba_sentences` |
| [Reverso Context](https://context.reverso.net) | Bilingual example sentences for words missing from Tatoeba | `more_sentences` |
| YouTube Data API v3 | Daily trending video comments from Israel | `youtube_comments_daily` |

---

## Scraping pipelines

`spider_dict` scrapes pealim.com page by page, collecting the base dictionary entry for each word (hebrew, transcription, root, part of speech, meaning, audio URL). It runs through three pipelines in parallel:

| Pipeline | Output | Notes |
|----------|--------|-------|
| `SQLPipeline` | MySQL `words` table | Flat row per entry, recreates table on each run (dev mode) |
| `MongoPipeline` | MongoDB `dict` collection | Batched inserts (100/batch) |
| `ExcelPipeline` | `dict_words.xlsx` | Full export via pandas |

`spider_words` takes the word URLs from `dict.json` and visits each one individually, dynamically extracting whatever conjugation or declension tables are present — verbs get full tense/person/gender conjugations, nouns get construct state and possessive forms, etc. The table structure varies by part of speech and is captured as-is. It runs through one pipeline:

| Pipeline | Output | Notes |
|----------|--------|-------|
| `WordsPipeline` | MongoDB `words_corrected` collection | Includes dynamic `tables` field with all inflection data, batched inserts |

Both spiders' outputs are merged into `dict-complete.json`, which becomes the dictionary source for the final dataset assembly.

---

## Database

The dataset is designed for **PostgreSQL with JSONB**:

```sql
CREATE TABLE vocab (
    word TEXT PRIMARY KEY,
    multiple_meanings BOOLEAN,
    data JSONB
);

CREATE INDEX ON vocab (multiple_meanings);
CREATE INDEX ON vocab USING GIN (data);
```

```python
import psycopg2, json

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

with open("data/vocab_dataset.json", encoding="utf-8") as f:
    entries = json.load(f)

for entry in entries:
    cur.execute(
        "INSERT INTO vocab (word, multiple_meanings, data) VALUES (%s, %s, %s) ON CONFLICT (word) DO UPDATE SET data = EXCLUDED.data",
        (entry["word"], entry["multiple_meanings"], json.dumps(entry, ensure_ascii=False))
    )

conn.commit()
```

---

## CI/CD

GitHub Actions (`.github/workflows/scraping.yaml`) runs the full test suite on every push and pull request. The daily pipeline (`make daily`) is not automated — run it manually when you want to refresh the trending data.

---

## License

MIT
