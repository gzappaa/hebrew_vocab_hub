import unittest
from pathlib import Path
from scrapy.http import HtmlResponse
from scraping.spiders.spider_dict import DictSpider

class TestDictSpiderLocal(unittest.TestCase):
    def setUp(self):
        self.spider = DictSpider()
        self.data_dir = Path(__file__).parent / "data"

    def test_parse_item_from_file(self):
        html_file = self.data_dir / "pealim.html"
        with open(html_file, "r", encoding="utf-8") as f:
            html = f.read()

        response = HtmlResponse(url='https://www.pealim.com/dict/', body=html, encoding='utf-8')
        items = list(self.spider.parse(response))

        self.assertTrue(len(items) > 0)
        first_item = items[0]
        self.assertIn('hebrew', first_item)
        self.assertIn('transcription', first_item)
        self.assertIn('part_of_speech', first_item)
        self.assertIn('meaning', first_item)
        self.assertIn('word_url', first_item)