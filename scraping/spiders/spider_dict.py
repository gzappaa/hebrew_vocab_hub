import scrapy
from scrapy.loader import ItemLoader
from scraping.items import DictItem

class DictSpider(scrapy.Spider):
    name = "dictspider"
    start_urls = ["https://www.pealim.com/dict/"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages_crawled = 0
        self.max_pages = 650  # tests

    def parse(self, response):
        self.pages_crawled += 1
        print(f"Page {self.pages_crawled}")  # simple logging to track progress

        base_url = "https://www.pealim.com"
        rows = response.css("table.dict-table-t tbody tr")

        for row in rows:
            loader = ItemLoader(item=DictItem(), selector=row)
            loader.add_css('hebrew', 'span.menukad::text')

            trans_nodes = row.xpath(".//span[@class='dict-transcription']//text()").getall()
            trans = ''.join(t.strip() for t in trans_nodes if t.strip()) if trans_nodes else '-'
            loader.add_value('transcription', trans)

            roots = row.xpath(".//td/a[contains(@href,'num-radicals')]/text()").getall()
            loader.add_value('root', ' - '.join(r.strip() for r in roots if r.strip()) if roots else '-')

            pos_nodes = row.xpath("td[3]//text()").getall()
            pos_text = ' '.join(p.strip() for p in pos_nodes if p.strip())
            loader.add_value('part_of_speech', pos_text if pos_text else '-')

            loader.add_css('meaning', 'td.dict-meaning::text')
            loader.add_css('audio_url', 'span.audio-play::attr(data-audio)')

            word_url = row.xpath(".//span[@class='menukad']/parent::a/@href").get()
            full_url = f"{base_url}{word_url}" if word_url else ''
            loader.add_value('word_url', full_url)

            yield loader.load_item()

        # --- next page ---
        if self.pages_crawled < self.max_pages:
            pagination_active = response.css("div.pagination ul.pagination li.active a::attr(href)").get()
            if pagination_active:
                current_page = int(pagination_active.split('=')[-1])
                next_page_number = current_page + 1
                next_page = response.css(
                    f'div.pagination ul.pagination li a[href*="?page={next_page_number}"]::attr(href)'
                ).get()
                if next_page:
                    yield response.follow(next_page, callback=self.parse)