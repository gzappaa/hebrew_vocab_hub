import json
from pathlib import Path


# project structure anchor
BASE_DIR = Path(__file__).resolve().parents[2]


INPUT_FILE = BASE_DIR / "dict-complete.json"
OUTPUT_FILE = BASE_DIR / "data" / "hebrew_words_RAW.json"


def extract_all_hebrew(obj, out_list):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "hebrew" and isinstance(v, str):
                out_list.append(v.strip())
            else:
                extract_all_hebrew(v, out_list)

    elif isinstance(obj, list):
        for item in obj:
            extract_all_hebrew(item, out_list)


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    words = []
    extract_all_hebrew(data, words)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)

    print("TOTAL BRUTO:", len(words))


if __name__ == "__main__":
    main()