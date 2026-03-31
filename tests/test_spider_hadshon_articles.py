import unittest
from pathlib import Path
from scrapy.http import HtmlResponse, Request
from scraping.spiders.spider_hadshon_articles import HadshonArticlesSpider
from scraping.items import ArticleItem

FIXTURES_DIR = Path(__file__).parent / "data" / "fixtures" / "htmls" / "hadshon_articles"


def fake_response(fixture_file, url, meta=None):
    html = (FIXTURES_DIR / fixture_file).read_bytes()
    request = Request(url=url, meta=meta or {})
    return HtmlResponse(url=url, request=request, body=html)


class TestParseListing(unittest.TestCase):

    def setUp(self):
        self.spider = HadshonArticlesSpider()

    def test_yields_article_requests(self):
        response = fake_response(
            "listing_page.html",
            url="https://hadshon.education.gov.il/articles/?page=1",
            meta={"page": 1},
        )
        results = list(self.spider.parse_listing(response))
        requests = [r for r in results if isinstance(r, Request)]
        self.assertGreater(len(requests), 0)

    def test_yields_next_page_request(self):
        response = fake_response(
            "listing_page.html",
            url="https://hadshon.education.gov.il/articles/?page=1",
            meta={"page": 1},
        )
        results = list(self.spider.parse_listing(response))
        requests = [r for r in results if isinstance(r, Request)]
        next_page = [r for r in requests if "page=2" in r.url]
        self.assertEqual(len(next_page), 1)

    def test_stops_on_empty_listing(self):
        response = fake_response(
            "listing_empty.html",
            url="https://hadshon.education.gov.il/articles/?page=999",
            meta={"page": 999},
        )
        results = list(self.spider.parse_listing(response))
        self.assertEqual(results, [])


class TestParseArticle(unittest.TestCase):

    def setUp(self):
        self.spider = HadshonArticlesSpider()

    def test_yields_article_item(self):
        response = fake_response(
            "article_page.html",
            url="https://hadshon.education.gov.il/articles/passover-is-holiday-of-freedom/",
        )
        results = list(self.spider.parse_article(response))
        items = [r for r in results if isinstance(r, ArticleItem)]
        self.assertEqual(len(items), 1)

    def test_item_fields_present(self):
        response = fake_response(
            "article_page.html",
            url="https://hadshon.education.gov.il/articles/passover-is-holiday-of-freedom/",
        )
        results = list(self.spider.parse_article(response))
        item = next(r for r in results if isinstance(r, ArticleItem))

        self.assertIn("title", item)
        self.assertIn("category", item)
        self.assertIn("audio_urls", item)
        self.assertIn("text", item)
        self.assertIn("word_explanations", item)

    def test_title_not_empty(self):
        response = fake_response(
            "article_page.html",
            url="https://hadshon.education.gov.il/articles/passover-is-holiday-of-freedom/",
        )
        results = list(self.spider.parse_article(response))
        item = next(r for r in results if isinstance(r, ArticleItem))
        self.assertNotEqual(item["title"], "")

    def test_text_not_empty(self):
        response = fake_response(
            "article_page.html",
            url="https://hadshon.education.gov.il/articles/passover-is-holiday-of-freedom/",
        )
        results = list(self.spider.parse_article(response))
        item = next(r for r in results if isinstance(r, ArticleItem))
        self.assertNotEqual(item["text"], "")

    def test_audio_urls_is_list(self):
        response = fake_response(
            "article_page.html",
            url="https://hadshon.education.gov.il/articles/passover-is-holiday-of-freedom/",
        )
        results = list(self.spider.parse_article(response))
        item = next(r for r in results if isinstance(r, ArticleItem))
        self.assertIsInstance(item["audio_urls"], list)

    def test_audio_urls_can_be_empty(self):
        response = fake_response(
            "article_no_audio.html",
            url="https://hadshon.education.gov.il/articles/some-article/",
        )
        results = list(self.spider.parse_article(response))
        item = next(r for r in results if isinstance(r, ArticleItem))
        self.assertIsInstance(item["audio_urls"], list)
        self.assertEqual(len(item["audio_urls"]), 0)

    def test_word_explanations_is_list(self):
        response = fake_response(
            "article_page.html",
            url="https://hadshon.education.gov.il/articles/passover-is-holiday-of-freedom/",
        )
        results = list(self.spider.parse_article(response))
        item = next(r for r in results if isinstance(r, ArticleItem))
        self.assertIsInstance(item["word_explanations"], list)

    def test_text_stops_before_biur_milim(self):
        response = fake_response(
            "article_page.html",
            url="https://hadshon.education.gov.il/articles/passover-is-holiday-of-freedom/",
        )
        results = list(self.spider.parse_article(response))
        item = next(r for r in results if isinstance(r, ArticleItem))
        self.assertNotIn("ביאורי מילים", item["text"])


class TestAllArticleFixtures(unittest.TestCase):

    def setUp(self):
        self.spider = HadshonArticlesSpider()

    def test_all_article_fixtures_parse_without_error(self):
        html_files = [
            f for f in FIXTURES_DIR.glob("*.html")
            if f.stem.startswith("article_") and f.stem != "article_no_audio"
        ]
        self.assertGreater(len(html_files), 0, "Nenhum HTML de artigo encontrado")

        for html_file in html_files:
            with self.subTest(file=html_file.name):
                response = fake_response(
                    html_file.name,
                    url=f"https://hadshon.education.gov.il/articles/{html_file.stem}/",
                )
                results = list(self.spider.parse_article(response))
                items = [r for r in results if isinstance(r, ArticleItem)]
                self.assertGreater(len(items), 0, f"Nenhum item extraído de {html_file.name}")


if __name__ == "__main__":
    unittest.main()