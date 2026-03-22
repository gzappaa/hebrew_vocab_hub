import unittest
from unittest.mock import MagicMock, patch
from scraping.pipelines import SQLPipeline

class TestSQLPipeline(unittest.TestCase):

    @patch('mysql.connector.connect')
    def setUp(self, mock_connect):
        """Setup a pipeline instance with a mocked MySQL connection and cursor."""
        # Mock connection and cursor
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = self.mock_cursor
        mock_connect.return_value = self.mock_conn

        # Create pipeline and open spider (which will use mocked conn/cursor)
        self.pipeline = SQLPipeline()
        self.pipeline.open_spider(spider=None)

    def test_process_item_inserts_correctly(self):
        """Ensure that process_item executes the correct SQL with proper values."""
        item = {
            'hebrew': 'שלום',
            'transcription': 'shalom',
            'root': 'ש-ל-ם',
            'part_of_speech': 'noun',
            'meaning': 'peace',
            'audio_url': 'http://audio.mp3',
            'word_url': 'http://word.url'
        }

        result = self.pipeline.process_item(item, spider=None)

        # Check that cursor.execute was called with correct SQL and params
        self.mock_cursor.execute.assert_called_with(
            """
            INSERT INTO words (hebrew, transcription, root, part_of_speech, meaning, audio_url, word_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
            ('שלום', 'shalom', 'ש-ל-ם', 'noun', 'peace', 'http://audio.mp3', 'http://word.url')
        )

        # Check that connection.commit() was called
        self.mock_conn.commit.assert_called()

        # The returned item should be the same
        self.assertEqual(result, item)

    def test_process_item_defaults(self):
        """Ensure defaults are used if some keys are missing in the item."""
        item = {}  # empty item

        result = self.pipeline.process_item(item, spider=None)

        # Check that cursor.execute was called with defaults
        self.mock_cursor.execute.assert_called_with(
            """
            INSERT INTO words (hebrew, transcription, root, part_of_speech, meaning, audio_url, word_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
            ('', '', '-', '', '', '', '')
        )

        self.assertEqual(result, item)

    def tearDown(self):
        """Close spider (mocked connection)."""
        self.pipeline.close_spider(spider=None)
        self.mock_conn.close.assert_called()

if __name__ == '__main__':
    unittest.main()