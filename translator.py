import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

EXPECTED_COLUMNS = [
    'Date', 'Address', 'Product', 'ASIN', 'Model_Requirements',
    'Total_Video', 'Scene', 'Pets_Kids', 'Requirements', 'Comments'
]

def retry_with_backoff(func, retries=3, base_delay=1.0, max_delay=5.0):
    for attempt in range(retries):
        try:
            return func()
        except Exception as e:
            if attempt == retries - 1:
                raise e
            delay = min(base_delay * (2 ** attempt), max_delay) + random.uniform(0, 1)
            time.sleep(delay)

def translate_column_deepl(df, col, translator):
    import logging
    logger = logging.getLogger()

    if col not in df.columns:
        logger.warning(f"Column '{col}' not found, skipping.")
        return df

    df[col] = df[col].astype(str).fillna('')
    mask = df[col] != ""
    texts_to_translate = df.loc[mask, col].tolist()

    if not texts_to_translate:
        logger.info(f"No non-empty values to translate in column '{col}'.")
        return df

    logger.info(f"Translating {len(texts_to_translate)} entries in column '{col}' using DeepL...")

    try:
        translations = translator.translate_text(texts_to_translate, target_lang="EN-US")
        df.loc[mask, col] = [t.text for t in translations]
    except Exception as e:
        logger.error(f"DeepL translation failed for column '{col}': {e}")

    return df

def translate_column_deepseek(df, col, api_key, max_workers):
    import logging
    logger = logging.getLogger()

    if col not in df.columns:
        logger.warning(f"Column '{col}' not found, skipping.")
        return df

    df[col] = df[col].astype(str).fillna('')
    mask = df[col] != ""
    texts_to_translate = df.loc[mask, col].tolist()

    if not texts_to_translate:
        logger.info(f"No non-empty values to translate in column '{col}'.")
        return df

    logger.info(f"Translating {len(texts_to_translate)} entries in column '{col}' using DeepSeek with {max_workers} threads...")

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    def translate_text(text):
        def call_api():
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": (
                        "You are a professional, accurate, and natural translator. "
                        "Do not add any introductions, commentary, or explanations. Only output the translated English text."
                    )},
                    {"role": "user", "content": f"Translate this Chinese text to fluent English:\n\n{text}"}
                ],
                stream=False
            )
            return response.choices[0].message.content.strip()

        try:
            return retry_with_backoff(call_api)
        except Exception as e:
            logger.error(f"DeepSeek translation failed for text: {e}")
            return text  # fallback

    translated = [None] * len(texts_to_translate)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(translate_text, text): idx for idx, text in enumerate(texts_to_translate)}
        for future in as_completed(futures):
            idx = futures[future]
            translated[idx] = future.result()

    df.loc[mask, col] = translated
    return df
