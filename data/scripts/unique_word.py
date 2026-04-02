import json
from pathlib import Path
import re

# --- paths ---
root = Path(__file__).parent.parent
data_dir = root               # pasta data
data_dir.mkdir(exist_ok=True)           # garante que a pasta exista

lyrics_file = root / "all_lyrics.txt"          # TXT de letras
articles_file = root / "articles.json"        # JSON de artigos
trending_file = root / "trending_daily.json"  # JSON de comentários
output_file = data_dir / "unique_words.txt"   # salva dentro de data

# --- regex para pegar só caracteres hebraicos ---
hebrew_re = re.compile(r'[\u0590-\u05FF]+')

# --- set para palavras únicas ---
unique_words = set()

# ---- Parte 1: letras de música ----
with open(lyrics_file, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        words = hebrew_re.findall(line)
        unique_words.update(words)

# ---- Parte 2: artigos ----
with open(articles_file, "r", encoding="utf-8") as f:
    articles = json.load(f)  # assume lista de JSONs
    for item in articles:
        text_to_process = item.get("title", "") + " " + item.get("text", "")
        words = hebrew_re.findall(text_to_process)
        unique_words.update(words)

# ---- Parte 3: comentários trending ----
with open(trending_file, "r", encoding="utf-8") as f:
    videos = json.load(f)  # lista de vídeos
    for video in videos:
        comments = video.get("comments", [])
        for comment in comments:
            text = comment.get("text", "")
            words = hebrew_re.findall(text)
            unique_words.update(words)

# ---- salvar resultado ----
unique_words_list = sorted(unique_words)

with open(output_file, "w", encoding="utf-8") as f:
    for word in unique_words_list:
        f.write(word + "\n")

print(f"Total unique Hebrew words from all sources: {len(unique_words_list)}")
print(f"Saved to: {output_file}")