import scrapy
import json
import os
import re


class LyricsSpider(scrapy.Spider):
    name = "lyrics"
    allowed_domains = ["genius.com"]

    custom_settings = {
        "ITEM_PIPELINES": {},  # explicitly disable all pipelines
    }

    def start_requests(self):
        # path to the JSON file with songs
        json_path = r"C:\hebrew_vocab_hub\data\hebrew_songs_genius.json"

        # load the JSON file
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # only process songs
        for song in data:
            # make a request for each song URL
            yield scrapy.Request(
                url=song["url"],
                callback=self.parse_lyrics,
                meta={
                    "artist": song["artist"],
                    "title": song["title"],
                }
            )

    def parse_lyrics(self, response):
        # get artist and title from meta
        artist = response.meta["artist"]
        title = response.meta["title"]

        # extract all lyric containers
        lyrics_parts = response.css("div[data-lyrics-container='true']::text").getall()

        # join all text pieces into a single string
        lyrics = "\n".join(lyrics_parts)

        # remove [Chorus], [Verse], etc.
        lyrics = re.sub(r"\[.*?\]", "", lyrics)

        # remove Unicode directional formatting characters (e.g., U+202A, U+202B, U+202C)
        lyrics = re.sub(r"[\u202A-\u202E]", "", lyrics)

        # remove extra empty lines
        lyrics = re.sub(r"\n\s*\n", "\n\n", lyrics).strip()

        # create the output directory if it does not exist
        output_dir = r"C:\hebrew_vocab_hub\data\songs"
        os.makedirs(output_dir, exist_ok=True)

        # sanitize filenames to remove invalid characters
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
        safe_artist = re.sub(r'[\\/*?:"<>|]', "", artist)

        # full path for the TXT file
        file_path = os.path.join(output_dir, f"{safe_artist} - {safe_title}.txt")

        # write the lyrics to the TXT file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"{title} - {artist}\n\n")
            f.write(lyrics)

        # log info about saved file
        self.logger.info(f"Saved: {file_path}")