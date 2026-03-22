import unittest
from scrapy.loader import ItemLoader
from scraping.items import DictItem

class TestDictItem(unittest.TestCase):

    def test_strip_and_takefirst(self):
        """Test that strip_text + TakeFirst works on the hebrew field"""
        loader = ItemLoader(item=DictItem())
        loader.add_value('hebrew', '  שלום  ')
        item = loader.load_item()
        self.assertEqual(item['hebrew'], 'שלום')

    def test_transcription_join(self):
        """Test that MapCompose + Compose(join_transcription) correctly joins transcription pieces"""
        loader = ItemLoader(item=DictItem())
        loader.add_value('transcription', ['  sha', 'lom  '])
        item = loader.load_item()
        self.assertEqual(item['transcription'], 'shalom')

    def test_root_field(self):
        """Test processing of the root field"""
        loader = ItemLoader(item=DictItem())
        loader.add_value('root', '  ש-ל-ם ')
        item = loader.load_item()
        self.assertEqual(item['root'], 'ש-ל-ם')

    def test_part_of_speech_field(self):
        """Test processing of the part_of_speech field"""
        loader = ItemLoader(item=DictItem())
        loader.add_value('part_of_speech', '  noun ')
        item = loader.load_item()
        self.assertEqual(item['part_of_speech'], 'noun')

    def test_meaning_field(self):
        """Test processing of the meaning field"""
        loader = ItemLoader(item=DictItem())
        loader.add_value('meaning', '  peace ')
        item = loader.load_item()
        self.assertEqual(item['meaning'], 'peace')

    def test_take_first_multiple_values(self):
        """Test that TakeFirst only takes the first value"""
        loader = ItemLoader(item=DictItem())
        loader.add_value('hebrew', ['שלום', 'ignored'])
        item = loader.load_item()
        self.assertEqual(item['hebrew'], 'שלום')

if __name__ == '__main__':
    unittest.main()