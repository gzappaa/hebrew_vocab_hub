import json
import time
import logging
import requests
import random
from pathlib import Path

# ---------------------------
# Paths
# ---------------------------
ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
SCRIPTS_DIR = DATA_DIR / "scripts"

DATA_PATH = DATA_DIR / "common_words.json"
OUTPUT_PATH = DATA_DIR / "sentences_tatoeba.json"
MISSING_PATH = DATA_DIR / "missing.json"
LOG_PATH = SCRIPTS_DIR / "log.txt"

# ---------------------------
# Logging
# ---------------------------
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ---------------------------
# API
# ---------------------------
API_URL = "https://tatoeba.org/en/api_v0/search"
MAX_SENTENCES = 3

session = requests.Session()

# ---------------------------
# STATE
# ---------------------------
COOLDOWN_UNTIL = 0
BASE_DELAY = 2.0
last_request_time = 0

# ---------------------------
# rate limit + jitter
# ---------------------------
def rate_limit():
    global last_request_time

    now = time.time()
    wait = BASE_DELAY - (now - last_request_time)

    if wait > 0:
        time.sleep(wait + random.uniform(0.3, 1.0))

    last_request_time = time.time()

# ---------------------------
# FETCH (corrigido)
# ---------------------------
def fetch(word):
    global COOLDOWN_UNTIL

    params = {
        "query": word,
        "from": "heb",
        "to": "eng",
        "page": 1
    }

    attempt = 0

    while True:
        if time.time() < COOLDOWN_UNTIL:
            wait = int(COOLDOWN_UNTIL - time.time())
            logging.info(f"COOLDOWN ACTIVE → sleeping {wait}s")
            time.sleep(wait)

        rate_limit()

        try:
            r = session.get(API_URL, params=params, timeout=15)

            # -----------------------
            # OK RESPONSE
            # -----------------------
            if r.status_code == 200:
                data = r.json()

                # 🔥 SE NÃO TEM RESULTADO → NÃO FICA INSISTINDO
                if not data.get("results"):
                    return None

                return data

            # -----------------------
            # RATE LIMIT
            # -----------------------
            if r.status_code == 429:
                wait = 600
                logging.warning(f"429 → sleeping {wait}s ({word})")
                COOLDOWN_UNTIL = time.time() + wait
                time.sleep(wait)
                continue

            logging.warning(f"HTTP {r.status_code} → retrying {word}")

        except requests.exceptions.Timeout:
            wait = min(30, 2 ** attempt)
            logging.warning(f"timeout → retry in {wait}s ({word})")
            time.sleep(wait)

        except Exception as e:
            wait = min(30, 2 ** attempt)
            logging.error(f"error {word}: {e} → retry in {wait}s")
            time.sleep(wait)

        attempt += 1

# ---------------------------
# load words
# ---------------------------
with open(DATA_PATH, "r", encoding="utf-8") as f:
    words = json.load(f)

output = []
missing_words = []
seen = set()

# ---------------------------
# main loop
# ---------------------------
i = 0
while i < len(words):
    word = words[i]

    if time.time() < COOLDOWN_UNTIL:
        wait = int(COOLDOWN_UNTIL - time.time())
        logging.info(f"COOLDOWN ACTIVE → sleeping {wait}s")
        time.sleep(wait)
        continue

    logging.info(f"{i+1}/{len(words)} {word}")

    data = fetch(word)

    if not data:
        missing_words.append({
            "word": word,
            "reason": "no_sentence"
        })
    else:
        found = False

        for item in data.get("results", [])[:MAX_SENTENCES]:
            heb = item.get("text")
            trans = item.get("translations", [])

            eng = None
            if trans and isinstance(trans[0], list) and trans[0]:
                eng = trans[0][0].get("text")

            if heb and eng and heb not in seen:
                seen.add(heb)

                output.append({
                    "word": word,
                    "sentence": heb,
                    "translation": eng
                })
                found = True

        if not found:
            missing_words.append({
                "word": word,
                "reason": "no_valid_translation"
            })

    # ---------------------------
    # CHECKPOINT (AGORA A CADA 10)
    # ---------------------------
    if i % 10 == 0:
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False)

        with open(MISSING_PATH, "w", encoding="utf-8") as f:
            json.dump(missing_words, f, ensure_ascii=False)

        logging.info("checkpoint saved")

    i += 1

# ---------------------------
# FINAL SAVE
# ---------------------------
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False)

with open(MISSING_PATH, "w", encoding="utf-8") as f:
    json.dump(missing_words, f, ensure_ascii=False)

logging.info("DONE")