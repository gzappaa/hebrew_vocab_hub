import scrapy
from urllib.parse import quote
from ..items import HadshonItem


class HadshonSpider(scrapy.Spider):
    name = "hadshon"
    allowed_domains = ["hadshon.education.gov.il"]

    custom_settings = {
        "ITEM_PIPELINES": {},
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1,
        "AUTOTHROTTLE_MAX_DELAY": 5,
        "FEEDS": {
            "data/hadshon.json": {
                "format": "json",
                "encoding": "utf8",
                "indent": 2,
            }
        }
    }

    CATEGORIES = {
        "words": "lexicons/words-and-concepts",
        "abbreviations": "lexicons/acronyms-and-abbreviations",
        "proverbs": "lexicons/proverbs",
        "people": "lexicons/people",
    }

    hebrew_letters = [
        "א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט",
        "י", "כ", "ל", "מ", "נ", "ס", "ע", "פ", "צ",
        "ק", "ר", "ש", "ת"
    ]

    BASE = "https://hadshon.education.gov.il"

    async def start(self):
        for category, path in self.CATEGORIES.items():
            for letter in self.hebrew_letters:
                url = f"{self.BASE}/{path}/?page=1&letter={quote(letter)}"
                yield scrapy.Request(
                    url,
                    callback=self.parse_letter,
                    meta={"category": category, "letter": letter, "page": 1},
                )

    def _url(self, path, letter, page):
        return f"{self.BASE}/{path}/?page={page}&letter={quote(letter)}"

    def parse_letter(self, response):
        category = response.meta["category"]
        letter = response.meta["letter"]
        page = response.meta["page"]
        path = self.CATEGORIES[category]

        if response.css("div.contentByLetterContainer div").re_first(r"לא נמצאו תוצאות"):
            self.logger.info(f"[{category}] {letter} ended by page {page}")
            return

        items = response.css("ul.contentByLetter li.introBlock")

        if not items:
            self.logger.info(f"[{category}] {letter} ended by page {page} (vazia)")
            return

        for li in items:
            hebrew = li.css("h3.termName::text").get("").strip()
            audio_url = li.css("audio source::attr(src)").get("") or ""

            text_parts = li.css("div.definition div.text *::text").getall()
            text = " ".join(t.strip() for t in text_parts if t.strip())

            more_parts = li.css("div.moreText *::text").getall()
            more_info = " ".join(t.strip() for t in more_parts if t.strip())

            yield HadshonItem(
                category=category,
                letter=letter,
                hebrew=hebrew,
                audio_url=audio_url,
                text=text,
                more_info=more_info,
            )

        self.logger.info(f"[{category}] {letter} | página {page} | {len(items)} itens")

        yield scrapy.Request(
            self._url(path, letter, page + 1),
            callback=self.parse_letter,
            meta={"category": category, "letter": letter, "page": page + 1},
        )