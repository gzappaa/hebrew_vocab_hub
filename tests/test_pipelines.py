import unittest
from unittest.mock import MagicMock, patch
from scraping.pipelines import SQLPipeline, ExcelPipeline, MongoPipeline

# ---------------------- SQL PIPELINE ----------------------
class TestSQLPipeline(unittest.TestCase):

    @patch('mysql.connector.connect')
    def setUp(self, mock_connect):
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = self.mock_cursor
        mock_connect.return_value = self.mock_conn

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


if __name__ == "__main__":
    unittest.main()