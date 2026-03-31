import unittest
import re
from pathlib import Path
from scrapy.http import HtmlResponse, Request
from scraping.spiders.spider_lyrics import LyricsSpider


class TestLyricsSpiderLocal(unittest.TestCase):

    def setUp(self):
        self.spider = LyricsSpider()
        self.html_path = Path(__file__).parent / "data" / "fixtures" / "htmls" / "lyrics.html"
        self.songs_dir = Path(__file__).parent.parent / "data" / "songs"
        self.songs_dir.mkdir(parents=True, exist_ok=True)

    def test_parse_lyrics_local(self):
        request = Request(
            url="http://test.com/song",
            meta={"artist": "Test Artist", "title": "Test Song"}
        )
        response = HtmlResponse(
            url=request.url,
            body=self.html_path.read_bytes(),
            request=request,
        )

        self.spider.parse_lyrics(response)

        safe_title = re.sub(r'[\\/*?:"<>|]', "", "Test Song")
        safe_artist = re.sub(r'[\\/*?:"<>|]', "", "Test Artist")
        file_path = self.songs_dir / f"{safe_artist} - {safe_title}.txt"

        self.assertTrue(file_path.exists())
        file_path.unlink()  # remove after


if __name__ == "__main__":
    unittest.main()