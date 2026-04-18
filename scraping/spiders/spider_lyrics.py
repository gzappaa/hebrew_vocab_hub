from pathlib import Path
import scrapy
import json
import re


class LyricsSpider(scrapy.Spider):
    name = "lyrics"
    allowed_domains = ["genius.com"]

    custom_settings = {
        "ITEM_PIPELINES": {},
    }

    def start_requests(self):
        root = Path(__file__).resolve().parents[2] 
        json_path = root / "data" / "hebrew_songs_genius.json"

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for song in data:
            yield scrapy.Request(
                url=song["url"],
                callback=self.parse_lyrics,
                meta={
                    "artist": song["artist"],
                    "title": song["title"],
                }
            )

    def parse_lyrics(self, response):
        artist = response.meta["artist"]
        title = response.meta["title"]

        lyrics_parts = response.css("div[data-lyrics-container='true']::text").getall()
        lyrics = "\n".join(lyrics_parts)

        lyrics = re.sub(r"\[.*?\]", "", lyrics)
        lyrics = re.sub(r"[\u202A-\u202E]", "", lyrics)
        lyrics = re.sub(r"\n\s*\n", "\n\n", lyrics).strip()

        root = Path(__file__).resolve().parents[2]
        output_dir = root / "data" / "songs"
        output_dir.mkdir(parents=True, exist_ok=True)

        safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
        safe_artist = re.sub(r'[\\/*?:"<>|]', "", artist)

        file_path = output_dir / f"{safe_artist} - {safe_title}.txt"

        file_path.write_text(
            f"{title} - {artist}\n\n{lyrics}",
            encoding="utf-8"
        )

        self.logger.info(f"Saved: {file_path}")