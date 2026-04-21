import scrapy
from ..items import ArticleItem


class HadshonArticlesSpider(scrapy.Spider):
    name = "hadshon_articles"
    allowed_domains = ["hadshon.education.gov.il"]

    custom_settings = {
        "ITEM_PIPELINES": {},
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1,
        "AUTOTHROTTLE_MAX_DELAY": 5,
        "FEEDS": {
            "data/hadshon_articles.json": {
                "format": "json",
                "encoding": "utf8",
                "indent": 2,
            }
        }
    }

    BASE = "https://hadshon.education.gov.il"

    async def start(self):
        yield scrapy.Request(
            f"{self.BASE}/articles/?page=1",
            callback=self.parse_listing,
            meta={"page": 1},
        )

    def parse_listing(self, response):
        page = response.meta["page"]
        cards = response.css(".catalogItemContainer")

        if not cards:
            self.logger.info(f"Listagem finalizada na página {page}")
            return

        for card in cards:
            url = card.css("h2.insideTitle a::attr(href)").get("")
            if url:
                yield scrapy.Request(
                    self.BASE + url,
                    callback=self.parse_article,
                    dont_filter=True,
                )

        self.logger.info(f"Listagem página {page} | {len(cards)} artigos")

        yield scrapy.Request(
            f"{self.BASE}/articles/?page={page + 1}",
            callback=self.parse_listing,
            meta={"page": page + 1},
        )

    def parse_article(self, response):
        title = response.css("h1::text").get("").strip()
        category = response.css(".itemDetails .value::text").get("").strip()
        audio = response.css("audio source::attr(src)").get("") or ""

        text_parts = []
        for p in response.css(".content p"):
            p_text = " ".join(t.strip() for t in p.css("*::text").getall() if t.strip())
            if "ביאורי מילים" in p_text:
                before = p_text.split("ביאורי מילים")[0].strip()
                if before:
                    text_parts.append(before)
                break
            if p_text:
                text_parts.append(p_text)

        text = " ".join(text_parts)

        word_explanations = [
            " ".join(t.strip() for t in li.css("::text").getall() if t.strip())
            for li in response.css(".content ul li")
        ]

        audio_urls = response.css("audio source::attr(src)").getall()

        yield ArticleItem(
            title=title,
            category=category,
            audio_urls=audio_urls,
            text=text,
            word_explanations=word_explanations,
        )

        self.logger.info(f"Article: {title[:60]}")