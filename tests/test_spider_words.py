import unittest
from pathlib import Path
from scrapy.http import HtmlResponse
from scrapy import Request
from scraping.spiders.spider_words import DetailspiderSpider

class TestDetailSpiderLocal(unittest.TestCase):
    def setUp(self):
        self.spider = DetailspiderSpider()
        self.html_dir = Path(__file__).parent / "data" / "fixtures" / "htmls" / "pealimpages"

    def test_parse_all_local_htmls(self):
        html_files = list(self.html_dir.glob("*.html"))
        self.assertTrue(len(html_files) > 0, "No HTML files found in data/htmls/")

        for html_file in html_files:
            with open(html_file, "r", encoding="utf-8") as f:
                html = f.read()

            # Create a response simulating a Scrapy request
            response = HtmlResponse(
                url=html_file.resolve().as_uri(),
                body=html.encode('utf-8'),  # must be bytes
                encoding='utf-8'
            )

            # Dummy item to pass in meta
            dummy_item = {"word_url": f"file://{html_file}"}

            # Attach a dummy request with meta
            response.request = Request(url=response.url, meta={"item": dummy_item})

            # Call parse_word of the spider
            items = list(self.spider.parse_word(response))

            # Should generate at least 1 item
            self.assertTrue(len(items) > 0, f"No items extracted from {html_file.name}")
            for item in items:
                # Tables should exist
                self.assertIn("tables", item)
                for table in item["tables"]:
                    self.assertIn("headers", table)
                    self.assertIn("rows", table)
                    for row in table["rows"]:
                        self.assertIn("cells", row)
                        for cell in row["cells"]:
                            self.assertIn("hebrew", cell)
                            self.assertIn("transcription", cell)
                            self.assertIn("meaning", cell)

if __name__ == "__main__":
    unittest.main()