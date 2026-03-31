import unittest
from pathlib import Path
from scrapy.http import HtmlResponse, Request
from scraping.spiders.spider_dict import DictSpider
from scraping.items import DictItem


class TestDictSpiderLocal(unittest.TestCase):

    def setUp(self):
        self.spider = DictSpider()
        html = (Path(__file__).parent / "data" / "fixtures" / "htmls" / "pealim.html").read_bytes()
        request = Request(url="https://www.pealim.com/dict/")
        self.response = HtmlResponse(url="https://www.pealim.com/dict/", request=request, body=html)
        self.results = list(self.spider.parse(self.response))

    def test_yields_items(self):
        items = [r for r in self.results if isinstance(r, DictItem)]
        self.assertGreater(len(items), 0)

    def test_item_fields_present(self):
        items = [r for r in self.results if isinstance(r, DictItem)]
        first = items[0]
        self.assertIn("hebrew", first)
        self.assertIn("transcription", first)
        self.assertIn("part_of_speech", first)
        self.assertIn("meaning", first)
        self.assertIn("word_url", first)

    def test_hebrew_not_empty(self):
        items = [r for r in self.results if isinstance(r, DictItem)]
        self.assertTrue(all(item.get("hebrew") for item in items))

    def test_yields_next_page_request(self):
        from scrapy.http import Request as ScrapyRequest
        requests = [r for r in self.results if isinstance(r, ScrapyRequest)]
        self.assertEqual(len(requests), 1)
        self.assertIn("page=", requests[0].url)