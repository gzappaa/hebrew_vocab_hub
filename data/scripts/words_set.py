import json
from pathlib import Path
import re
import unicodedata

# --- paths ---
root = Path(__file__).parent.parent
data_dir = root
data_dir.mkdir(exist_ok=True)  # garante que a pasta exista

unique_words_file = data_dir / "unique_words.txt"
hebrew_words_file = data_dir / "hebrew_words.json"
output_file = data_dir / "common_words.json"

# --- regex para remover qualquer caractere que não seja letra hebraica ---
non_hebrew_re = re.compile(r'[^\u0590-\u05FF]')

# --- função para limpar palavra: remove nekudot e caracteres não hebraicos ---
def clean_word(word):
    # decompor e remover diacríticos (nekudot)
    no_nekud = ''.join(c for c in unicodedata.normalize('NFD', word)
                       if not unicodedata.combining(c))
    # remover qualquer caractere que não seja hebraico
    return non_hebrew_re.sub('', no_nekud)

# --- carregar unique_words.txt e limpar ---
with open(unique_words_file, "r", encoding="utf-8") as f:
    unique_words_set = set(clean_word(line.strip()) for line in f if line.strip())

# --- carregar hebrew_words.json e limpar ---
with open(hebrew_words_file, "r", encoding="utf-8") as f:
    hebrew_words_list = json.load(f)
hebrew_words_set = set(clean_word(word) for word in hebrew_words_list)

# --- interseção dos dois sets ---
common_words = sorted(unique_words_set & hebrew_words_set)

# --- salvar resultado em JSON na pasta data ---
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(common_words, f, ensure_ascii=False, indent=2)

print(f"Total words in both sources after cleaning: {len(common_words)}")
print(f"Saved to: {output_file}")