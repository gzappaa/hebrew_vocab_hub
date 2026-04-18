Date: 24/03
Decision: Use response.follow for pagination instead of generating requests manually.
Reason: The website may add multiple new words or pages dynamically. Using response.follow ensures the spider automatically follows the next page links as they appear, preventing potential breakage if the total number of pages changes. This approach is safer and more maintainable than hardcoding page URLs.


Date: 28/03
Decision: Use MongoDB Pipeline for storing words with dynamic tables.
Reason: Some words (especially verbs) have conjugation tables with different numbers of rows/columns, and other words may have no table at all. MongoDB allows storing arrays of subdocuments (tables, headers, rows, cells) without worrying about a rigid schema. This makes it perfect for capturing all variations dynamically and scaling to thousands of words, unlike SQL which would require multiple joins or custom columns.

Date: 29/03
Decision: Start building a selective Hebrew word dataset from popular sources, focusing initially on songs.
Reason: Out of 240,000 Hebrew words collected, it’s necessary to prioritize the most frequent and relevant words. Using Spotify Israel top tracks (2018‑2026) filtered for Hebrew, combined with Genius API for lyrics, allows extraction of natural language examples. Creating .txt files per song and shuffling lines prevents copyright issues while preserving usable phrases for word analysis and dataset building.

Date: 15/04
Decision: Use a more conservative request strategy when consuming the Tatoeba API.
Reason: I was getting a lot of rate limits (HTTP 429) from the Tatoeba API, so I reduced the request speed and added cooldowns and retries. It’s not very efficient, but it’s more stable and avoids getting blocked.

Date: 17/04
Decision: Use a more conservative request strategy when consuming the Tatoeba API.
Reason: I was getting a lot of rate limits (HTTP 429) from the Tatoeba API, so I reduced the request speed and added cooldowns and retries. It’s not very efficient, but it’s more stable and avoids getting blocked.


remember - .json name