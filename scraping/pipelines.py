import mysql.connector
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()  # load .env variables

class SQLPipeline:
    def open_spider(self, spider):
        self.conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DB"),
            charset='utf8mb4'
        )
        self.cursor = self.conn.cursor()
        # force UTF-8 encoding for Hebrew characters
        self.cursor.execute("SET NAMES utf8mb4;")
        self.cursor.execute("SET CHARACTER SET utf8mb4;")
        self.cursor.execute("SET character_set_connection=utf8mb4;")
        # create table if it doesn't exist, now with root
        self.cursor.execute("DROP TABLE IF EXISTS words")  # drop table for testing
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

    def close_spider(self, spider):
        self.conn.close()

    def process_item(self, item, spider):
        hebrew = item.get('hebrew', '')
        transcription = item.get('transcription', '')
        root = item.get('root', '-')
        part_of_speech = item.get('part_of_speech', '')
        meaning = item.get('meaning', '')
        audio_url = item.get('audio_url', '')
        word_url = item.get('word_url', '')

        sql = """
            INSERT INTO words (hebrew, transcription, root, part_of_speech, meaning, audio_url, word_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        self.cursor.execute(sql, (hebrew, transcription, root, part_of_speech, meaning, audio_url, word_url))
        self.conn.commit()
        return item
    

class ExcelPipeline:
    def __init__(self):
        # let's keep items in memory and write to Excel at the end
        self.items = []

    def open_spider(self, spider):
        """Called when the spider starts."""
        self.items = []  # clear items list at the start of the spider

    def close_spider(self, spider):
        """Called when the spider finishes."""
        # convert list of dicts to DataFrame
        df = pd.DataFrame(self.items)

        # save to Excel
        df.to_excel("dict_words.xlsx", index=False)
        print(f"Saved {len(self.items)} items to dict_words.xlsx")

    def process_item(self, item, spider):
        """Called for every item scraped by the spider."""
        # convert item to dict and append to items list
        self.items.append(dict(item))
        return item