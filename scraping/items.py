import scrapy
from itemloaders.processors import Compose, MapCompose, TakeFirst

def strip_text(value):
    return value.strip() if value else value


def join_transcription(values):
    # values is a list of strings, we want to join them into one string
    return ''.join(values).strip() if values else ''


def normalize_dash(value):
    if value:
        return value.replace("–", "-").strip()
    return value




class DictItem(scrapy.Item):
    hebrew = scrapy.Field(
        input_processor=MapCompose(strip_text),
        output_processor=TakeFirst()
    )
    transcription = scrapy.Field(
        input_processor=MapCompose(strip_text),   
        output_processor=Compose(join_transcription) 
    )
    root = scrapy.Field(
        input_processor=MapCompose(strip_text),
        output_processor=TakeFirst()
    )
    part_of_speech = scrapy.Field(
        input_processor=MapCompose(strip_text, normalize_dash),
        output_processor=TakeFirst()
    )
    meaning = scrapy.Field(
        input_processor=MapCompose(strip_text),
        output_processor=TakeFirst()
    )
    audio_url = scrapy.Field(output_processor=TakeFirst())
    word_url = scrapy.Field(output_processor=TakeFirst())



class HadshonItem(scrapy.Item):  
    category = scrapy.Field()  # words, abbreviations, proverbs, people
    letter   = scrapy.Field()  # א, ב, etc
    hebrew   = scrapy.Field()
    audio_url = scrapy.Field()
    text     = scrapy.Field()
    more_info = scrapy.Field()

class ArticleItem(scrapy.Item):
    title             = scrapy.Field()
    category          = scrapy.Field()
    audio_urls        = scrapy.Field()  # list
    text              = scrapy.Field()
    word_explanations = scrapy.Field()