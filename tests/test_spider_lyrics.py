import unittest
import os
import re
from scrapy.http import HtmlResponse, Request
from scraping.spiders.spider_lyrics import LyricsSpider  # importa sua spider normalmente



class TestLyricsSpiderLocal(unittest.TestCase):
    def setUp(self):
        self.spider = LyricsSpider()
        # html local for testing
        self.html_path = os.path.join(os.path.dirname(__file__), "data", "lyrics.html")
        # file structure 
        self.test_dir = os.path.dirname(__file__)  # ...\hebrew_vocab_hub\tests
        self.root_dir = os.path.abspath(os.path.join(self.test_dir, "..")) 
        self.songs_dir = os.path.join(self.root_dir, "data", "songs")
        os.makedirs(self.songs_dir, exist_ok=True)

    def test_parse_lyrics_local(self):
        # read the local HTML file
        with open(self.html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # create a fake Request with meta for artist and title
        request = Request(
            url="http://test.com/song",
            meta={"artist": "Test Artist", "title": "Test Song"}
        )

        # create a fake Response
        response = HtmlResponse(
            url=request.url,
            body=html_content,
            encoding="utf-8",
            request=request
        )

        # call the spider's parse_lyrics method
        self.spider.parse_lyrics(response)

        # safe file name
        safe_title = re.sub(r'[\\/*?:"<>|]', "", "Test Song")
        safe_artist = re.sub(r'[\\/*?:"<>|]', "", "Test Artist")
        file_path = os.path.join(self.songs_dir, f"{safe_artist} - {safe_title}.txt")

        # check if the file was created
        self.assertTrue(os.path.exists(file_path))
 

        # remove the created file after test
        os.remove(file_path)


if __name__ == "__main__":
    unittest.main()