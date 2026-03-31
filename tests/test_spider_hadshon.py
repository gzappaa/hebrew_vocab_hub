import unittest
from pathlib import Path
from scrapy.http import HtmlResponse, Request
from scraping.spiders.spider_hadshon import HadshonSpider
from scraping.items import HadshonItem

FIXTURES_DIR = Path(__file__).parent / "data" / "fixtures" / "htmls" / "hadshon"

def fake_response(fixture_file, url, meta):
    html = (FIXTURES_DIR / fixture_file).read_bytes()
    request = Request(url=url, meta=meta)
    return HtmlResponse(url=url, request=request, body=html)


class TestParseLetterWords(unittest.TestCase):

    def setUp(self):
        self.spider = HadshonSpider()

    def test_yields_items_words(self):
        response = fake_response(
            "words.html",
            url="https://hadshon.education.gov.il/lexicons/words-and-concepts/?page=1&letter=%D7%90",
            meta={"category": "words", "letter": "א", "page": 1},
        )
        results = list(self.spider.parse_letter(response))
        items = [r for r in results if isinstance(r, HadshonItem)]
        self.assertGreater(len(items), 0)

    def test_yields_items_abbreviations(self):
        response = fake_response(
            "abbreviations.html",
            url="https://hadshon.education.gov.il/lexicons/acronyms-and-abbreviations/?page=1&letter=%D7%90",
            meta={"category": "abbreviations", "letter": "א", "page": 1},
        )
        results = list(self.spider.parse_letter(response))
        items = [r for r in results if isinstance(r, HadshonItem)]
        self.assertGreater(len(items), 0)

    def test_yields_items_proverbs(self):
        response = fake_response(
            "proverbs.html",
            url="https://hadshon.education.gov.il/lexicons/proverbs/?page=1&letter=%D7%90",
            meta={"category": "proverbs", "letter": "א", "page": 1},
        )
        results = list(self.spider.parse_letter(response))
        items = [r for r in results if isinstance(r, HadshonItem)]
        self.assertGreater(len(items), 0)

    def test_yields_items_people(self):
        response = fake_response(
            "people.html",
            url="https://hadshon.education.gov.il/lexicons/people/?page=1&letter=%D7%90",
            meta={"category": "people", "letter": "א", "page": 1},
        )
        results = list(self.spider.parse_letter(response))
        items = [r for r in results if isinstance(r, HadshonItem)]
        self.assertGreater(len(items), 0)

    def test_item_fields_present(self):
        response = fake_response(
            "words.html",
            url="https://hadshon.education.gov.il/lexicons/words-and-concepts/?page=1&letter=%D7%90",
            meta={"category": "words", "letter": "א", "page": 1},
        )
        results = list(self.spider.parse_letter(response))
        item = next(r for r in results if isinstance(r, HadshonItem))

        self.assertNotEqual(item["hebrew"], "")
        self.assertEqual(item["category"], "words")
        self.assertEqual(item["letter"], "א")
        self.assertNotEqual(item["text"], "")

    def test_yields_next_page_request(self):
        response = fake_response(
            "words.html",
            url="https://hadshon.education.gov.il/lexicons/words-and-concepts/?page=1&letter=%D7%90",
            meta={"category": "words", "letter": "א", "page": 1},
        )
        results = list(self.spider.parse_letter(response))
        requests = [r for r in results if isinstance(r, Request)]

        self.assertEqual(len(requests), 1)
        self.assertIn("page=2", requests[0].url)

    def test_audio_url_present_in_all_items(self):
        for fixture, category, url in [
            ("words.html", "words", "https://hadshon.education.gov.il/lexicons/words-and-concepts/?page=1&letter=%D7%90"),
            ("abbreviations.html", "abbreviations", "https://hadshon.education.gov.il/lexicons/acronyms-and-abbreviations/?page=1&letter=%D7%90"),
            ("proverbs.html", "proverbs", "https://hadshon.education.gov.il/lexicons/proverbs/?page=1&letter=%D7%90"),
            ("people.html", "people", "https://hadshon.education.gov.il/lexicons/people/?page=1&letter=%D7%90"),
        ]:
            with self.subTest(category=category):
                response = fake_response(fixture, url=url, meta={"category": category, "letter": "א", "page": 1})
                results = list(self.spider.parse_letter(response))
                items = [r for r in results if isinstance(r, HadshonItem)]
                self.assertTrue(all("audio_url" in item for item in items))


class TestParseLetterEmpty(unittest.TestCase):

    def setUp(self):
        self.spider = HadshonSpider()

    def test_stops_on_no_results(self):
        response = fake_response(
            "words_empty.html",
            url="https://hadshon.education.gov.il/lexicons/words-and-concepts/?page=99&letter=%D7%90",
            meta={"category": "words", "letter": "א", "page": 99},
        )
        results = list(self.spider.parse_letter(response))
        self.assertEqual(results, [])

    def test_stops_on_empty_list(self):
        response = fake_response(
            "words_empty.html",
            url="https://hadshon.education.gov.il/lexicons/words-and-concepts/?page=99&letter=%D7%90",
            meta={"category": "words", "letter": "א", "page": 99},
        )
        results = list(self.spider.parse_letter(response))
        self.assertEqual(len([r for r in results if isinstance(r, Request)]), 0)


class TestAllFixtures(unittest.TestCase):

    def setUp(self):
        self.spider = HadshonSpider()

    def test_all_fixtures_parse_without_error(self):
        html_files = [f for f in FIXTURES_DIR.glob("*.html") if f.stem != "words_empty"]
        self.assertGreater(len(html_files), 0, "Nenhum HTML encontrado em fixtures/htmls/hadshon")

        category_map = {
            "words":         "https://hadshon.education.gov.il/lexicons/words-and-concepts/?page=1&letter=%D7%90",
            "abbreviations": "https://hadshon.education.gov.il/lexicons/acronyms-and-abbreviations/?page=1&letter=%D7%90",
            "proverbs":      "https://hadshon.education.gov.il/lexicons/proverbs/?page=1&letter=%D7%90",
            "people":        "https://hadshon.education.gov.il/lexicons/people/?page=1&letter=%D7%90",
        }

        for html_file in html_files:
            with self.subTest(file=html_file.name):
                category = html_file.stem
                url = category_map.get(category, f"https://hadshon.education.gov.il/lexicons/{category}/?page=1&letter=%D7%90")
                response = fake_response(
                    html_file.name,
                    url=url,
                    meta={"category": category, "letter": "א", "page": 1},
                )
                results = list(self.spider.parse_letter(response))
                items = [r for r in results if isinstance(r, HadshonItem)]
                self.assertIsInstance(items, list)


if __name__ == "__main__":
    unittest.main()