# 🇮🇱 hebrew_vocab_hub

> A large-scale Hebrew vocabulary data pipeline — scraping, processing, and enriching Hebrew words from dictionaries, government educational sites, trending media, song lyrics, and real-world corpora into a clean, sentence-rich dataset.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Pipeline Architecture](#pipeline-architecture)
  - [Phase 1 — Dictionary Scraping](#phase-1--dictionary-scraping)
  - [Phase 2 — Media & Lyrics Collection](#phase-2--media--lyrics-collection)
  - [Phase 3 — Trending & Real-World Data](#phase-3--trending--real-world-data)
  - [Phase 4 — Vocabulary Intersection](#phase-4--vocabulary-intersection)
  - [Phase 5 — Sentence Enrichment](#phase-5--sentence-enrichment)
- [Output Files](#output-files)
- [Setup & Installation](#setup--installation)
- [Running the Pipeline](#running-the-pipeline)
- [Testing](#testing)
- [CI/CD](#cicd)
- [Configuration](#configuration)
- [Tech Stack](#tech-stack)

---

## Overview

`hebrew_vocab_hub` automates the collection and enrichment of Hebrew vocabulary by combining multiple heterogeneous data sources:

- **Structured dictionaries** (Pealim) — morphology, conjugation tables, word classes
- **Government educational content** (Hadshon) — curated vocabulary and news articles
- **Popular music** — top Spotify Israel tracks with scraped lyrics
- **Trending language** — daily YouTube comments from popular Israeli videos
- **Sentence databases** — Tatoeba and Reverso for real-world usage examples

The end result is a rich dataset of ~12,500 high-frequency Hebrew words, each grounded in real media usage and enriched with translated example sentences.

---

## Project Structure

```
hebrew_vocab_hub/
├── scraping/
│   ├── spiders/
│   │   ├── spider_dict.py          # Pealim dictionary scraper
│   │   ├── spider_words.py         # Word conjugation table scraper
│   │   ├── spider_hadshon.py       # Hadshon vocabulary scraper
│   │   ├── spider_hadshon_articles.py  # Hadshon news articles scraper
│   │   └── spider_lyrics.py        # Genius lyrics scraper
│   ├── items.py
│   ├── pipelines.py
│   ├── middlewares.py
│   └── settings.py
├── data/
│   ├── scripts/
│   │   ├── hebrew_song_filter.py   # Filter Hebrew songs from Spotify chart
│   │   ├── musicfinder.py          # Resolve song URLs via Genius API
│   │   ├── lyrics_scrambler.py     # Merge & shuffle lyrics into corpus
│   │   ├── unique_word.py          # Extract unique words from all corpora
│   │   ├── words.py                # Flatten all word forms into RAW list
│   │   ├── words_set.py            # Intersect unique_words with RAW list
│   │   ├── tatoeba_sentences.py    # Fetch sentences from Tatoeba API
│   │   ├── more_sentences.py       # Fetch missing sentences via Reverso (Playwright)
│   │   ├── youtube_comments_daily.py  # Collect trending YouTube comments
│   │   └── state.py                # State tracker for resumable runs
│   ├── common_words.json
│   ├── hebrew_words_RAW.json
│   ├── hebrew_songs.json
│   ├── hebrew_songs_genius.json
│   ├── hadshon.json
│   ├── hadshon_articles.json
│   ├── sentences_tatoeba.json
│   ├── sentences_reverso.json
│   ├── missing.json
│   ├── unique_words.txt
│   └── all_lyrics.txt
├── tests/
│   ├── test_items.py
│   ├── test_pipelines.py
│   ├── test_spider_dict.py
│   ├── test_spider_hadshon.py
│   ├── test_spider_hadshon_articles.py
│   ├── test_spider_lyrics.py
│   └── test_spider_words.py
├── .github/
│   └── workflows/
│       └── scraping.yaml           # CI/CD pipeline
├── dict.json
├── state.json
├── requirements.txt
└── scrapy.cfg
```

---

## Pipeline Architecture

### Phase 1 — Dictionary Scraping

#### `spider_dict` · `scraping/spiders/spider_dict.py`

Crawls [pealim.com/words](https://pealim.com/words) page by page, extracting every entry with its word, grammatical class, meaning, and metadata. Results are persisted to MongoDB, SQL, and Excel, and exported as **`dict.json`**.

#### `spider_words` · `scraping/spiders/spider_words.py`

Reads the word URLs from `dict.json` and visits each word's dedicated page, dynamically extracting all available inflection/conjugation tables (verb binyanim, noun declensions, etc.). Outputs all forms to feed the next stage.

#### `data/scripts/words.py`

Processes all scraped word pages and flattens every conjugated and inflected form into a single raw list. Produces **`hebrew_words_RAW.json`** — ~235,000 word forms.

---

### Phase 2 — Media & Lyrics Collection

#### `spider_hadshon` · `scraping/spiders/spider_hadshon.py`

Scrapes [Hadshon](https://hadshon.co.il) — an Israeli government platform for Hebrew learners — collecting vocabulary entries, abbreviations, notable people, proverbs, and more. Outputs **`hadshon.json`**.

#### `spider_hadshon_articles` · `scraping/spiders/spider_hadshon_articles.py`

Scrapes the news article section of Hadshon, collecting article content for corpus use. Outputs **`hadshon_articles.json`**.

#### `data/scripts/hebrew_song_filter.py`

Takes the Spotify Weekly Chart totals for Israel (top ~2,000 tracks since 2018) and filters for songs with Hebrew in the title. Outputs **`hebrew_songs.json`**.

#### `data/scripts/musicfinder.py`

For each song in `hebrew_songs.json`, queries the Genius API to resolve the lyrics page URL. Outputs **`hebrew_songs_genius.json`**.

#### `spider_lyrics` · `scraping/spiders/spider_lyrics.py`

Reads `hebrew_songs_genius.json` and scrapes the full lyrics for each track from Genius, stripping structural annotations (e.g., `[Chorus]`, `[Verse 1]`). Saves one `.txt` file per song under `data/songs/`.

#### `data/scripts/lyrics_scrambler.py`

Merges all individual song `.txt` files into a single corpus, then shuffles line order to break song-level structure while preserving sentence integrity. Outputs **`all_lyrics.txt`**.

---

### Phase 3 — Trending & Real-World Data

#### `data/scripts/youtube_comments_daily.py`

Uses the YouTube Data API to fetch comments from the most-viewed Israeli videos of the day. Outputs a dated snapshot — e.g., **`trending_23-03-2026.json`** (configurable).

#### `data/scripts/unique_word.py`

Aggregates all text sources — `hadshon_articles.json`, `all_lyrics.txt`, and the trending JSON — and extracts every unique Hebrew word token. Outputs **`unique_words.txt`**.

> ⚠️ To use a different trending file, update the `trending_file` variable in `unique_word.py`:
> ```python
> trending_file = root / "trending_23-03-2026.json"  # change to your file
> ```

---

### Phase 4 — Vocabulary Intersection

#### `data/scripts/words_set.py`

Intersects `unique_words.txt` (words seen in real media) with `hebrew_words_RAW.json` (all known morphological forms). The result is a deduplicated, frequency-grounded vocabulary set of **~12,500 words**, exported as **`common_words.json`**.

---

### Phase 5 — Sentence Enrichment

#### `data/scripts/tatoeba_sentences.py`

Queries the [Tatoeba](https://tatoeba.org) API for each of the 12,500 words, fetching up to 3 translated example sentences per word while respecting Tatoeba's rate limits. Achieves coverage for ~9,000 words. Outputs **`sentences_tatoeba.json`** and **`missing.json`** (the remaining ~3,000 uncovered words).

#### `data/scripts/state.py`

Generates **`state.json`** to track progress across resumable runs. Required before running `more_sentences.py`.

#### `data/scripts/more_sentences.py`

Processes the ~3,000 words in `missing.json` using [Playwright](https://playwright.dev/) to intercept Reverso's private API, fetching 3 translated sentences per word. Falls back to DOM scraping when the API is unavailable. Outputs **`sentences_reverso.json`**.

---

## Output Files

| File | Description |
|------|-------------|
| `dict.json` | All dictionary entries from Pealim |
| `data/hebrew_words_RAW.json` | ~235k raw word forms (all inflections) |
| `data/hadshon.json` | Vocabulary from Hadshon (government learner site) |
| `data/hadshon_articles.json` | News articles from Hadshon |
| `data/hebrew_songs.json` | Filtered Hebrew songs from Spotify Israel chart |
| `data/hebrew_songs_genius.json` | Songs enriched with Genius lyrics URLs |
| `data/all_lyrics.txt` | Full lyrics corpus (shuffled line order) |
| `data/unique_words.txt` | All unique word tokens from media corpora |
| `data/common_words.json` | ~12,500 high-frequency validated Hebrew words |
| `data/sentences_tatoeba.json` | Example sentences for ~9,000 words (Tatoeba) |
| `data/sentences_reverso.json` | Example sentences for remaining ~3,000 words (Reverso) |
| `data/missing.json` | Words with no Tatoeba coverage (input for Reverso step) |
| `trending_<date>.json` | Daily YouTube trending word snapshot |

---

## Setup & Installation

### Prerequisites

- Python 3.10+
- Node.js (optional, for any JS tooling)
- MongoDB (for spider_dict pipeline persistence)
- A Chromium browser (for Playwright in `more_sentences.py`)

### Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### Environment variables

Copy `.env.example` to `.env` and fill in your API keys:

```env
GENIUS_API_TOKEN=your_genius_token
YOUTUBE_API_KEY=your_youtube_api_key
MONGO_URI=mongodb://localhost:27017
```

---

## Running the Pipeline

Run each stage in order. All scripts are designed to be idempotent and resumable.

```bash
# Phase 1 — Dictionary
scrapy crawl dict
scrapy crawl words
python data/scripts/words.py

# Phase 2 — Media & Lyrics
scrapy crawl hadshon
scrapy crawl hadshon_articles
python data/scripts/hebrew_song_filter.py
python data/scripts/musicfinder.py
scrapy crawl lyrics
python data/scripts/lyrics_scrambler.py

# Phase 3 — Trending
python data/scripts/youtube_comments_daily.py
python data/scripts/unique_word.py

# Phase 4 — Intersection
python data/scripts/words_set.py

# Phase 5 — Sentences
python data/scripts/tatoeba_sentences.py
python data/scripts/state.py
python data/scripts/more_sentences.py
```

---

## Testing

Unit tests cover all spiders, items, and pipelines using fixture HTML files.

```bash
pytest tests/
```

Test fixtures are located in `tests/data/fixtures/htmls/` and mirror real page structures from Pealim, Hadshon, and Genius.

---

## CI/CD

GitHub Actions is configured in `.github/workflows/scraping.yaml` to automate scheduled scraping runs and validate the pipeline on every push.

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| [Scrapy](https://scrapy.org) | Web scraping framework |
| [Playwright](https://playwright.dev/python/) | Browser automation for Reverso |
| [Genius API](https://docs.genius.com) | Song lyrics URL resolution |
| [YouTube Data API v3](https://developers.google.com/youtube/v3) | Daily trending comments |
| [Tatoeba API](https://tatoeba.org/en/api) | Sentence examples |
| MongoDB | Intermediate storage for dictionary data |
| GitHub Actions | CI/CD scheduling and automation |
| pytest | Unit testing |
