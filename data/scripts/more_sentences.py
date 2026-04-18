from pathlib import Path
import json
import re
import time
from playwright.sync_api import sync_playwright


# run tatoeba_sentences.py to generate missing.json, then run this to get sentences for those words
# run state.py first to save the necessary cookies from a logged-in session on context.reverso.net

# ======================
# PATHS
# ======================
ROOT_DIR    = Path(__file__).resolve().parents[2]
DATA_DIR    = ROOT_DIR / "data"
SCRIPTS_DIR = DATA_DIR / "scripts"

STATE_FILE  = ROOT_DIR / "state.json"
INPUT_FILE  = DATA_DIR / "missing.json"
OUTPUT_FILE = DATA_DIR / "sentences_reverso.json"
LOG_FILE    = SCRIPTS_DIR / "log.txt"

EXAMPLES_WANTED = 3

# ======================
# LOG
# ======================
def log(msg: str):
    print(msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

# ======================
# CLEAN
# ======================
def clean(text: str) -> str | None:
    if not text:
        return None
    return re.sub(r"</?em>", "", text).strip() or None

# ======================
# HTML EXTRACTOR
# ======================
def extract_from_html(page, word: str) -> list[tuple[str, str]]:
    # inclui .blocked — muitas palavras só têm exemplos bloqueados no HTML
    all_examples  = page.query_selector_all("#examples-content .example")
    free_examples = page.query_selector_all("#examples-content .example:not(.blocked)")

    log(f"  [HTML] total examples in DOM: {len(all_examples)}")
    log(f"  [HTML] non-blocked examples : {len(free_examples)}")

    if len(all_examples) == 0:
        log(f"  [HTML] #examples-content vazio ou ausente")
        return []

    if len(free_examples) == 0 and len(all_examples) > 0:
        log(f"  [HTML] TODOS os {len(all_examples)} exemplos estão .blocked — usando mesmo assim")

    # usa todos (blocked ou não) para não perder a palavra
    results = []
    for ex in all_examples:
        src_el = ex.query_selector(".src .text")
        trg_el = ex.query_selector(".trg .text")
        if not src_el or not trg_el:
            continue
        src = clean(src_el.inner_text())
        trg = clean(trg_el.inner_text())
        if src and trg:
            results.append((src, trg))

    log(f"  [HTML] pares válidos extraídos: {len(results)}")
    if results:
        log(f"  [HTML] primeiro par: {results[0][0][:60]} | {results[0][1][:60]}")

    return results

# ======================
# LOAD INPUT
# ======================
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    missing = json.load(f)
words = [x["word"] for x in missing if "word" in x]

# ======================
# LOAD OUTPUT (resume)
# ======================
if OUTPUT_FILE.exists():
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        results = json.load(f)
else:
    results = []

done_words = {r["word"] for r in results if "word" in r}
seen = {(r["word"], r["sentence"]) for r in results if r.get("sentence")}

# ======================
# SCRAPER
# ======================
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        storage_state=str(STATE_FILE) if STATE_FILE.exists() else None
    )
    page = context.new_page()

    current_word = {"value": None, "api_added": 0}

    def handle_response(response):
        if "bst-query-service" not in response.url:
            return

        word = current_word["value"]
        log(f"  [API] response capturada para: {word}")
        log(f"  [API] url: {response.url}")

        try:
            data     = response.json()
            examples = data.get("list", []) or []
            log(f"  [API] itens em 'list': {len(examples)}")

            if len(examples) == 0:
                log(f"  [API] chaves da resposta: {list(data.keys())}")

            added = 0
            for ex in examples:
                if added >= EXAMPLES_WANTED:
                    break
                sentence    = clean(ex.get("s_text"))
                translation = clean(ex.get("t_text"))
                if not sentence or not translation:
                    log(f"  [API] exemplo ignorado — s_text={ex.get('s_text')!r} t_text={ex.get('t_text')!r}")
                    continue
                key = (word, sentence)
                if key in seen:
                    log(f"  [API] duplicado ignorado: {sentence[:50]}")
                    continue
                seen.add(key)
                results.append({"word": word, "sentence": sentence, "translation": translation})
                added += 1
                log(f"  [API] ✔ adicionado ({added}): {sentence[:60]}")

            current_word["api_added"] = added
            log(f"  [API] total adicionado via API: {added}")

        except Exception as e:
            log(f"  [API] ❌ erro ao parsear resposta: {e}")
            current_word["api_added"] = 0

    page.on("response", handle_response)

    for i, word in enumerate(words, 1):
        if word in done_words:
            log(f"[{i}/{len(words)}] SKIP (já feito): {word}")
            continue

        current_word["value"]     = word
        current_word["api_added"] = 0

        log(f"\n{'='*50}")
        log(f"[{i}/{len(words)}] PALAVRA: {word}")
        log(f"{'='*50}")

        try:
            page.goto(
                f"https://context.reverso.net/translation/hebrew-english/{word}",
                wait_until="domcontentloaded"
            )

            try:
                page.click("text=Display more examples", timeout=5000)
                log(f"  [NAV] clicou em 'Display more examples'")
            except:
                log(f"  [NAV] botão 'Display more examples' não encontrado")

            page.wait_for_timeout(5000)

            # ------- fallback HTML se a API não entregou -------
            if current_word["api_added"] < EXAMPLES_WANTED:
                log(f"  [FALLBACK] API entregou {current_word['api_added']}/{EXAMPLES_WANTED} → tentando HTML")
                html_pairs = extract_from_html(page, word)
                fallback_added = 0
                for src, trg in html_pairs:
                    if current_word["api_added"] + fallback_added >= EXAMPLES_WANTED:
                        break
                    key = (word, src)
                    if key in seen:
                        continue
                    seen.add(key)
                    results.append({"word": word, "sentence": src, "translation": trg})
                    fallback_added += 1
                    log(f"  [FALLBACK] ✔ adicionado ({fallback_added}): {src[:60]}")

                total = current_word["api_added"] + fallback_added
                if total > 0:
                    log(f"  [FALLBACK] resultado final: {total} exemplos (api={current_word['api_added']} html={fallback_added})")
                else:
                    log(f"  [FALLBACK] ❌ zero exemplos para '{word}' — verifique a palavra")
            else:
                log(f"  [OK] API entregou {EXAMPLES_WANTED}/{EXAMPLES_WANTED}, sem fallback necessário")

            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            log(f"  [SAVE] output salvo ({len(results)} registros total)")

        except Exception as e:
            log(f"  ❌ ERRO GERAL para '{word}': {e}")

        time.sleep(3)

    browser.close()