# Hebrew Vocab Hub

Hebrew Vocab Hub is a Python project to collect, store, and manage Hebrew vocabulary. It uses **Scrapy** to extract words and their metadata from online sources and provides pipelines to save the data to **MySQL**, **MongoDB**, or **Excel** files.

The project also includes unit tests to ensure the scraper and pipelines work correctly.

---

## Project Structure
```
# hebrew_vocab_hub Project Structure

hebrew_vocab_hub/
│
├── .env                   # Environment variables (MongoDB, MySQL, etc.)
├── .gitignore
├── dict.json              # Vocabulary already extracted in JSON format
├── dict_words.xlsx        # Vocabulary saved as Excel
├── requirements.txt       # Project dependencies
├── scrapy.cfg             # Scrapy configuration
├── scrapy_full_log.txt    # Full Scrapy execution log
│
├── scraping/              # Main scraper code
│   ├── __init__.py
│   ├── items.py           # Scrapy Items definition
│   ├── middlewares.py
│   ├── pipelines.py       # Pipelines (SQL, MongoDB, Excel)
│   ├── settings.py        # Scrapy settings
│   └── spiders/
│       ├── __init__.py
│       ├── spider_dict.py # Main spider
│       └── __pycache__/...
│
└── tests/                 # Unit tests
    ├── __init__.py
    ├── test_items.py
    ├── test_pipelines.py
    ├── test_spider_dict.py
    └── data/
        └── dict.html   # HTML file for testing spiders


---

## Features

- **Scrapy Spider**: Crawls Hebrew vocabulary from online dictionaries and sources.  
- **SQL Pipeline**: Saves scraped words to a MySQL database.  
- **MongoDB Pipeline**: Stores scraped words in a MongoDB collection with batch insertion.  
- **Excel Pipeline**: Saves scraped words into an Excel file (`dict_words.xlsx`).  
- **Unit Tests**: Tests pipelines and spider functionality using `unittest` and `unittest.mock`.  

---

## Installation

1.  Clone the repository:

```
bash
git clone <repo_url>
cd hebrew_vocab_hub
```

2. Create a virtual environment and install dependencies:

```
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

3. Set your environment variables in .env for MySQL and MongoDB connections.

## Run Pipelines Separately (Optional)

You can use the pipelines independently in Python scripts:
```
from scraping.pipelines import SQLPipeline, MongoPipeline, ExcelPipeline

pipeline = ExcelPipeline()
pipeline.open_spider()
pipeline.process_item({'hebrew': 'שלום', 'transcription': 'shalom'})
pipeline.close_spider()
```
## Run unittests

```
python -m unittest discover
```