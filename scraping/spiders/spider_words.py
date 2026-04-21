import scrapy
import json
from pathlib import Path


class DetailspiderSpider(scrapy.Spider):
    name = "words"
    allowed_domains = ["pealim.com"]

    custom_settings = {
        "ITEM_PIPELINES": {
        },
        "FEEDS": {
            "dict-complete2.json": {
                "format": "json",
                "encoding": "utf8",
                "indent": 2,
            }
        }
    }

    def start_requests(self):
        # Project root: hebrew_vocab_hub
        ROOT_DIR = Path(__file__).resolve().parents[2]
        json_path = ROOT_DIR / "dict.json"

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            url = item.get("word_url")
            if url:
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_word,
                    meta={"item": item}
                )

    def parse_word(self, response):
        item = response.meta["item"]

        tables = response.css("table.conjugation-table")
        conjugations = []

        for table in tables:
            parsed_table = self.parse_table(table)
            if parsed_table:
                conjugations.append(parsed_table)

        item["tables"] = conjugations
        yield item

    def extract_hebrew(self, td):
        """
        Priority:
        1. chaser (modern Ktiv Male)
        2. menukad (niqqud / dictionary form fallback)
        """
        chaser = td.css("span.chaser::text").get()

        if chaser:
            return chaser.replace("~", "").strip()

        return td.css("span.menukad::text").get(default="").strip()

    def parse_table(self, table):
        result = {}

        headers = []
        for tr in table.css("thead tr"):
            row_headers = []
            for th in tr.css("th"):
                text = th.css("::text").get(default="").strip()
                colspan = int(th.attrib.get("colspan", 1))
                rowspan = int(th.attrib.get("rowspan", 1))
                row_headers.append({
                    "text": text,
                    "colspan": colspan,
                    "rowspan": rowspan
                })
            if row_headers:
                headers.append(row_headers)

        result["headers"] = headers

        rows_data = []
        for row in table.css("tbody tr"):
            row_dict = {}

            ths = [
                th.css("::text").get(default="").strip()
                for th in row.css("th")
                if th.css("::text").get()
            ]
            if ths:
                row_dict["labels"] = ths

            cells = []
            for td in row.css("td"):
                hebrew = self.extract_hebrew(td)
                transcription = "".join(td.css("div.transcription *::text").getall()).strip()
                meaning = "".join(td.css("div.meaning *::text").getall()).strip()

                cells.append({
                    "hebrew": hebrew,
                    "transcription": transcription,
                    "meaning": meaning
                })

            row_dict["cells"] = cells
            rows_data.append(row_dict)

        result["rows"] = rows_data
        return result