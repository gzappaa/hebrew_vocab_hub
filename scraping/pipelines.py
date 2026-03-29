import mysql.connector
import os
from dotenv import load_dotenv
import pandas as pd
from pymongo import MongoClient

load_dotenv()

# ---------------------- SQL PIPELINE ----------------------
class SQLPipeline:
    @classmethod
    def from_crawler(cls, crawler):
        # allows to access settings if needed: crawler.settings.get('MY_SETTING')
        return cls()

    def open_spider(self):
        self.conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DB"),
            charset='utf8mb4'
        )
        self.cursor = self.conn.cursor()

        # UTF-8 for Hebrew support
        self.cursor.execute("SET NAMES utf8mb4;")
        self.cursor.execute("SET CHARACTER SET utf8mb4;")
        self.cursor.execute("SET character_set_connection=utf8mb4;")

        # recreates table (dev mode)
        self.cursor.execute("DROP TABLE IF EXISTS words")

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id INT AUTO_INCREMENT PRIMARY KEY,
                hebrew VARCHAR(255),
                transcription VARCHAR(255),
                root VARCHAR(50),
                part_of_speech VARCHAR(255),
                meaning TEXT,
                audio_url VARCHAR(255),
                word_url VARCHAR(255)
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)

        self.conn.commit()

    def close_spider(self):
        self.cursor.close()
        self.conn.close()

    def process_item(self, item):
        sql = """
            INSERT INTO words 
            (hebrew, transcription, root, part_of_speech, meaning, audio_url, word_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        self.cursor.execute(sql, (
            item.get('hebrew', ''),
            item.get('transcription', ''),
            item.get('root', '-'),
            item.get('part_of_speech', ''),
            item.get('meaning', ''),
            item.get('audio_url', ''),
            item.get('word_url', '')
        ))
        self.conn.commit()
        return item


# ---------------------- EXCEL PIPELINE ----------------------
class ExcelPipeline:
    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def __init__(self):
        self.items = []

    def open_spider(self):
        self.items = []

    def close_spider(self):
        if not self.items:
            return

        df = pd.DataFrame(self.items)
        df.to_excel("dict_words.xlsx", index=False)
        print(f"Saved {len(self.items)} items to dict_words.xlsx")

    def process_item(self, item):
        self.items.append(dict(item))
        return item


# ---------------------- MONGO PIPELINE ----------------------
class MongoPipeline:
    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def open_spider(self):
        uri = os.getenv("MONGO_URI")
        if not uri:
            raise ValueError("MONGO_URI not found in .env")

        self.client = MongoClient(uri)
        self.db = self.client["hebrew_vocab_hub"]


        # buffer pra performance
        self.buffer = []
        self.batch_size = 100

    def close_spider(self):
        if self.buffer:
            self.db["dict"].insert_many(self.buffer)
        self.client.close()

    def process_item(self, item):
        doc = {
            "hebrew": item.get('hebrew', ''),
            "transcription": item.get('transcription', ''),
            "root": item.get('root', '-'),
            "part_of_speech": item.get('part_of_speech', ''),
            "meaning": item.get('meaning', ''),
            "audio_url": item.get('audio_url', ''),
            "word_url": item.get('word_url', '')
        }
        self.buffer.append(doc)

        if len(self.buffer) >= self.batch_size:
            self.db["dict"].insert_many(self.buffer)
            self.buffer = []

        return item


# ----------------------- MONGO PIPELINE 2.0 (with tables) ----------------------

class WordsPipeline:
    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def open_spider(self):
        uri = os.getenv("MONGO_URI")
        if not uri:
            raise ValueError("MONGO_URI not found in .env")

        self.client = MongoClient(uri)
        self.db = self.client["hebrew_vocab_hub"]
        # buffer for performance
        self.buffer = []
        self.batch_size = 100

    def close_spider(self):
        if self.buffer:
            self.db["words_corrected"].insert_many(self.buffer)
        self.client.close()

    def process_item(self, item):
        # mount the document with tables (if any)
        doc = {
            "hebrew": item.get("hebrew", ""),
            "transcription": item.get("transcription", ""),
            "root": item.get("root", "-"),
            "part_of_speech": item.get("part_of_speech", ""),
            "meaning": item.get("meaning", ""),
            "word_url": item.get("word_url", ""),
            "tables": item.get("tables", {})  # dynamic tables field from details spider
        }
        self.buffer.append(doc)

        if len(self.buffer) >= self.batch_size:
            self.db["words_corrected"].insert_many(self.buffer)
            self.buffer = []

        return item