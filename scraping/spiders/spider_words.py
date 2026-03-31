import scrapy
import json
import os


class DetailspiderSpider(scrapy.Spider):
    name = "spider_words"
    allowed_domains = ["pealim.com"]

    # === Custom settings: only runs WordsPipeline (if tiver) ===
    custom_settings = {
        'ITEM_PIPELINES': {
            'scraping.pipelines.WordsPipeline': 600
        }
    }

    def start_requests(self):
        # Load dict.json
        with open("dict.json", "r", encoding="utf-8") as f:
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

        # get all conjugation tables dynamically
        tables = response.css("table.conjugation-table")
        conjugations = []

        for table in tables:
            parsed_table = self.parse_table(table)
            if parsed_table:
                conjugations.append(parsed_table)

        # update the item with conjugation tables
        item["tables"] = conjugations
        yield item

    def parse_table(self, table):
        result = {}

        # --- dinamic headers  ---
        headers = []
        for tr in table.css("thead tr"):
            row_headers = []
            for th in tr.css("th"):
                text = th.css("::text").get(default="").strip()
                colspan = int(th.attrib.get("colspan", 1))
                rowspan = int(th.attrib.get("rowspan", 1))
                row_headers.append({"text": text, "colspan": colspan, "rowspan": rowspan})
            if row_headers:
                headers.append(row_headers)
        result["headers"] = headers

        # --- body of the table ---
        rows_data = []
        for row in table.css("tbody tr"):
            row_dict = {}

            # table headers (th)
            ths = [th.css("::text").get(default="").strip() for th in row.css("th") if th.css("::text").get()]
            if ths:
                row_dict["labels"] = ths

            # Cells
            cells = []
            for td in row.css("td"):
                hebrew = td.css("span.menukad::text").get(default="").strip()
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