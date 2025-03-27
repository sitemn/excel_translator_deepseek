import pandas as pd
import deepl
import logging
import os
import sys
import time
import random
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Configuration ---
INPUT_FILE = "test_data.xlsx"
OUTPUT_FILE = "translated_output.xlsx"
DEEPL_AUTH_KEY = os.getenv("DEEPL_AUTH_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
TARGET_LANG = "EN-US"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("translation.log", mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Expected columns
EXPECTED_COLUMNS = ['Date', 'Address', 'Product', 'ASIN', 'Model_Requirements', 'Total_Video', 'Scene', 'Pets_Kids', 'Requirements', 'Comments']

def retry_with_backoff(func, retries=3, base_delay=1.0, max_delay=5.0):
    for attempt in range(retries):
        try:
            return func()
        except Exception as e:
            if attempt == retries - 1:
                raise e
            delay = min(base_delay * (2 ** attempt), max_delay) + random.uniform(0, 1)
            time.sleep(delay)

def translate_column_deepl(df, col, translator, batch=False, batch_size=50):
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

    translated = []

    try:
        if not batch:
            translations = translator.translate_text(texts_to_translate, target_lang=TARGET_LANG)
            translated = [t.text for t in translations]
        else:
            for i in range(0, len(texts_to_translate), batch_size):
                chunk = texts_to_translate[i:i + batch_size]
                chunk_translations = translator.translate_text(chunk, target_lang=TARGET_LANG)
                translated.extend([t.text for t in chunk_translations])
    except Exception as e:
        logger.error(f"DeepL translation failed for column '{col}': {e}")
        return df

    df.loc[mask, col] = translated
    return df

def translate_column_deepseek(df, col, api_key, max_workers=5):
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
                        "You are a professional, accurate, and natural translator. \n"
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
            return text  # fallback to original

    # Perform translations in parallel
    translated = [None] * len(texts_to_translate)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(translate_text, text): idx for idx, text in enumerate(texts_to_translate)}
        for future in as_completed(futures):
            idx = futures[future]
            translated[idx] = future.result()

    df.loc[mask, col] = translated
    return df

def main():
    logger.info("Translation script started.")

    if not DEEPL_AUTH_KEY:
        logger.error("DEEPL_AUTH_KEY environment variable is not set.")
        sys.exit(1)

    if not DEEPSEEK_API_KEY:
        logger.error("DEEPSEEK_API_KEY environment variable is not set.")
        sys.exit(1)

    if not os.path.exists(INPUT_FILE):
        logger.error(f"Input file not found: {INPUT_FILE}")
        sys.exit(1)

    try:
        df = pd.read_excel(INPUT_FILE)
        logger.info(f"Loaded worksheet with {len(df)} rows.")
    except Exception as e:
        logger.error(f"Failed to read Excel file: {e}")
        sys.exit(1)

    # missing_cols = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    # if missing_cols:
    #     logger.error(f"Missing expected columns: {missing_cols}")
    #     sys.exit(1)

    df.columns = EXPECTED_COLUMNS

    # Preprocessing
    df['Model_Requirements'] = df['Model_Requirements'].fillna('N/A')
    df['Scene'] = df['Scene'].fillna('N/A').astype(str)
    df['Pets_Kids'] = df['Pets_Kids'].fillna('N/A').astype(str)
    df['Shooting_Requirements'] = (
        df['Comments'].fillna('').astype(str) + '\n' +
        df['Requirements'].fillna('').astype(str)
    )
    df.drop(columns=['Comments', 'Requirements'], inplace=True)

    # Initialize translators
    try:
        deepl_translator = deepl.Translator(DEEPL_AUTH_KEY)
    except Exception as e:
        logger.error(f"Failed to initialize DeepL translator: {e}")
        sys.exit(1)

    # Translate using DeepL
    for column in ['Product', 'Model_Requirements', 'Scene', 'Pets_Kids']:
        df = translate_column_deepl(df, column, deepl_translator, batch=False)

    # Translate using DeepSeek
    df = translate_column_deepseek(df, 'Shooting_Requirements', api_key=DEEPSEEK_API_KEY)

    # Format the Date column to avoid time component
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.strftime('%m/%d/%Y')

    # Output to Excel
    try:
        df.to_excel(OUTPUT_FILE, index=False)
        logger.info(f"Translation completed. Output saved to: {OUTPUT_FILE}")
    except Exception as e:
        logger.error(f"Failed to save output file: {e}")

    logger.info("Translation script finished.")

if __name__ == "__main__":
    main()
