import scrapy
from scrapy.loader import ItemLoader
from scraping.items import DictItem

class DictSpider(scrapy.Spider):
    name = "dictspider"
    start_urls = ["https://www.pealim.com/dict/"]

    def parse(self, response):
        rows = response.css("table.dict-table-t tbody tr")
        base_url = "https://www.pealim.com"

        for row in rows:
            loader = ItemLoader(item=DictItem(), selector=row)
            loader.add_css('hebrew', 'span.menukad::text')
            trans_nodes = row.xpath(".//span[@class='dict-transcription']//text()").getall()
            trans = ''.join(t.strip() for t in trans_nodes if t.strip()) if trans_nodes else '-'
            loader.add_value('transcription', trans)
            loader.add_value('root', '-')  # default

            roots = row.xpath(".//td/a[contains(@href,'num-radicals')]/text()").getall()
            if roots:
                loader.replace_value('root', ' - '.join(r.strip() for r in roots if r.strip()))

            pos_nodes = row.xpath("td[3]//text()").getall()  # get all texts inside the td 
            pos_text = ' '.join(p.strip() for p in pos_nodes if p.strip())  # merge them into one string
            loader.add_value('part_of_speech', pos_text if pos_text else '-')
            loader.add_css('meaning', 'td.dict-meaning::text')
            loader.add_css('audio_url', 'span.audio-play::attr(data-audio)')

            word_url = row.xpath(".//span[@class='menukad']/parent::a/@href").get()
            full_url = f"{base_url}{word_url}" if word_url else ''
            loader.add_value('word_url', full_url)

            yield loader.load_item()