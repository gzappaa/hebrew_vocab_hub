import unittest
from unittest.mock import MagicMock, patch
from scraping.pipelines import SQLPipeline, ExcelPipeline, MongoPipeline, WordsPipeline
import os



# ---------------------- SQL PIPELINE ----------------------
class TestSQLPipeline(unittest.TestCase):

    def setUp(self):
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = self.mock_cursor

        with patch('mysql.connector.connect', return_value=self.mock_conn):
            self.pipeline = SQLPipeline()
            self.pipeline.open_spider()

    def test_process_item_insert(self):
        item = {
            'hebrew': 'שלום',
            'transcription': 'shalom',
            'root': 'ש-ל-ם',
            'part_of_speech': 'noun',
            'meaning': 'peace',
            'audio_url': 'url',
            'word_url': 'url'
        }
        result = self.pipeline.process_item(item)

        # ✅ test if execute was called
        self.assertTrue(self.mock_cursor.execute.called)

        # Test if commit was called
        self.mock_conn.commit.assert_called()

        # Test if the returned item is the same
        self.assertEqual(result, item)

    def test_process_item_defaults(self):
        item = {}
        self.pipeline.process_item(item)
        args = self.mock_cursor.execute.call_args[0][1]
        self.assertEqual(args, ('', '', '-', '', '', '', ''))

    def test_close_spider(self):
        self.pipeline.close_spider()
        self.mock_conn.close.assert_called()


# ---------------------- EXCEL PIPELINE ----------------------
class TestExcelPipeline(unittest.TestCase):

    @patch("pandas.DataFrame.to_excel")
    def test_excel_save(self, mock_to_excel):
        pipeline = ExcelPipeline()
        pipeline.open_spider()

        pipeline.process_item({'hebrew': 'שלום'})
        pipeline.process_item({'hebrew': 'מים'})
        pipeline.close_spider()

        mock_to_excel.assert_called_once()
    
    def tearDown(self):
        if os.path.exists("dict_words.xlsx"):
            os.remove("dict_words.xlsx")


# ---------------------- MONGO PIPELINE ----------------------
class TestMongoPipeline(unittest.TestCase):

    @patch("scraping.pipelines.MongoClient")
    @patch("scraping.pipelines.os.getenv", return_value="mongodb://fake")
    def test_mongo_insert(self, mock_env, mock_client):
        mock_collection = MagicMock()
        mock_collection.delete_many.return_value = None
        mock_collection.insert_many.return_value = None

        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_client.return_value.__getitem__.return_value = mock_db

        pipeline = MongoPipeline()
        pipeline.open_spider()

        pipeline.process_item({'hebrew': 'שלום'})
        pipeline.close_spider()

        mock_collection.insert_many.assert_called()

    @patch("scraping.pipelines.MongoClient")
    @patch("scraping.pipelines.os.getenv", return_value="mongodb://fake")
    def test_mongo_buffer_flush(self, mock_env, mock_client):
        mock_collection = MagicMock()
        mock_collection.delete_many.return_value = None
        mock_collection.insert_many.return_value = None

        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_client.return_value.__getitem__.return_value = mock_db

        pipeline = MongoPipeline()
        pipeline.open_spider()
        pipeline.batch_size = 2  # force flush after 2 items
        pipeline.process_item({'hebrew': 'a'})
        pipeline.process_item({'hebrew': 'b'})

        mock_collection.insert_many.assert_called()


class TestWordsPipeline(unittest.TestCase):

    def setUp(self):
        self.mock_collection = MagicMock()
        self.mock_db = MagicMock()
        self.mock_db.__getitem__.return_value = self.mock_collection

        with patch("scraping.pipelines.MongoClient") as mock_client, \
            patch("scraping.pipelines.os.getenv", return_value="mongodb://fake"):
            mock_client.return_value.__getitem__.return_value = self.mock_db
            self.pipeline = WordsPipeline()
            self.pipeline.open_spider()

    def test_process_item_with_tables(self):
        # Item with tables
        item = {
            "hebrew": "שלום",
            "transcription": "shalom",
            "root": "ש-ל-ם",
            "part_of_speech": "noun",
            "meaning": "peace",
            "word_url": "url",
            "tables": [{"headers": ["Past", "Present"], "rows": [{"cells": [{"hebrew": "הלך"}]}]}]
        }

        result = self.pipeline.process_item(item)

        # Item returned unchanged
        self.assertEqual(result, item)
        # Buffer should contain the doc
        self.assertEqual(len(self.pipeline.buffer), 1)
        self.assertEqual(self.pipeline.buffer[0]["tables"], item["tables"])

    def test_process_item_defaults(self):
        # Item with missing fields
        item = {}
        result = self.pipeline.process_item(item)

        doc = self.pipeline.buffer[0]
        self.assertEqual(doc["hebrew"], "")
        self.assertEqual(doc["transcription"], "")
        self.assertEqual(doc["root"], "-")
        self.assertEqual(doc["tables"], {})

    def test_buffer_flush_on_batch_size(self):
        # Force small batch size for testing
        self.pipeline.batch_size = 2
        item1 = {"hebrew": "a"}
        item2 = {"hebrew": "b"}

        self.pipeline.process_item(item1)
        # Should not flush yet
        self.assertEqual(self.pipeline.buffer, [ 
            {
                "hebrew": "a",
                "transcription": "",
                "root": "-",
                "part_of_speech": "",
                "meaning": "",
                "word_url": "",
                "tables": {}
            }
        ])

        # Process second item -> should flush
        self.pipeline.process_item(item2)
        self.assertEqual(self.pipeline.buffer, [])
        self.pipeline.db["words"].insert_many.assert_called_once()

    def test_close_spider_flush_remaining(self):
        # Add item to buffer
        item = {"hebrew": "remaining"}
        self.pipeline.process_item(item)
        self.pipeline.close_spider()
        # Should flush remaining buffer
        self.pipeline.db["words_corrected"].insert_many.assert_called_once()
        self.pipeline.client.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()