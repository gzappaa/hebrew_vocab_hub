# Date: 24/03
## Decision: 
Use response.follow for pagination instead of generating requests manually.
## Reason:
The website may add multiple new words or pages dynamically. Using response.follow ensures the spider automatically follows the next page links as they appear, preventing potential breakage if the total number of pages changes. This approach is safer and more maintainable than hardcoding page URLs.

---

# Date: 28/03
## Decision: 
Use MongoDB Pipeline for storing words with dynamic tables.
## Reason:
Some words (especially verbs) have conjugation tables with different numbers of rows/columns, and other words may have no table at all. MongoDB allows storing arrays of subdocuments (tables, headers, rows, cells) without a rigid schema. This makes it suitable for capturing all variations dynamically and scaling to large datasets, unlike SQL which would require complex joins or schema redesigns.

---

# Date: 29/03
## Decision: 
Build a selective Hebrew word dataset focused on high-frequency sources (starting with songs).
## Reason:
From a large corpus (~240k words), prioritization is required. Using Spotify Israel top tracks (2018–2026) filtered for Hebrew, combined with Genius API lyrics, allows extraction of natural contextual usage. Splitting into .txt files per song and shuffling lines helps preserve usable data while reducing copyright risk and keeping the dataset diverse.

---

# Date: 15/04
## Decision: 
Introduce conservative request strategy for Tatoeba API ingestion.
## Reason:
The API was returning frequent HTTP 429 rate limits. To stabilize ingestion, request speed was reduced and retry/cooldown logic was added. This sacrifices speed for reliability and prevents blocking during large-scale collection.

---

# Date: 17/04
## Decision: 
Implement hybrid sentence scraping pipeline (Tatoeba API + Reverso API + HTML fallback) with deduplication and persistence.
## Reason:
Tatoeba API coverage was incomplete (~9k/12k required sentences). To fill gaps, Reverso was integrated via intercepted API responses (Playwright), with HTML parsing as fallback when API data was insufficient. Deduplication (seen set) prevents repetition, and incremental persistence ensures safe long-run execution without data loss.

---

# Date: 19/04
## Decision: 
Rebuild dataset to prioritize Ktiv Male (modern Hebrew orthography) as canonical form.
## Reason:
Initial pipeline incorrectly treated vocalized / niqqud-based forms (Ktiv Hasar) as primary entries instead of modern unvocalized Hebrew (Ktiv Male). This caused mismatch with real-world usage, where Ktiv Male dominates (~99% in everyday text such as media and messaging). The dataset was restructured to reflect actual contemporary Hebrew usage.

---

# Date: 21/04
## Decision: 
Implement normalized reverse-matching pipeline between common_words, dict-complete, and sentence corpora using niqqud-stripped Hebrew forms.
## Reason:
Hebrew without vowels is inherently ambiguous (e.g. חברה can map to multiple meanings). All dictionary entries were expanded into all observed Hebrew forms, normalized by stripping niqqud, and indexed for reverse lookup.

Each word from common_words is matched against this index to collect all possible meanings, while sentence datasets (Reverso + Tatoeba) are normalized the same way and attached per word. Deduplication ensures clean aggregation across sources.

## Result:
A scalable lexical dataset supporting multi-meaning lookup, sentence enrichment, and API-ready structure for downstream applications.