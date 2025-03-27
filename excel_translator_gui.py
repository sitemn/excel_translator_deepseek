#deepseek version with gui


import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
import threading
import pandas as pd
import logging
import os
import time
import random
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
import deepl
import sys

# --- Logger Setup ---
class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.configure(state='normal')
        self.text_widget.insert(tk.END, msg + '\n')
        self.text_widget.configure(state='disabled')
        self.text_widget.yview(tk.END)

logger = logging.getLogger("translator_gui")
logger.setLevel(logging.INFO)

EXPECTED_COLUMNS = ['Date', 'Address', 'Product', 'ASIN', 'Model_Requirements', 'Total_Video', 'Scene', 'Pets_Kids', 'Requirements', 'Comments']

# --- Translation Helpers ---
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

# --- GUI App ---
class TranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Excel Translator App")
        self.root.geometry("800x600")
        self.root.configure(padx=15, pady=15)

        style = ttk.Style()
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("TEntry", font=("Segoe UI", 10))

        self.create_widgets()
        self.setup_logger()

    def create_widgets(self):
        frame = ttk.Frame(self.root)
        frame.pack(fill='x', pady=5)

        ttk.Label(frame, text="Excel File:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        self.file_entry = ttk.Entry(frame, width=50)
        self.file_entry.grid(row=0, column=1, padx=5)
        ttk.Button(frame, text="Browse", command=self.browse_file).grid(row=0, column=2, padx=5)

        ttk.Label(frame, text="DeepL API Key:").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        self.deepl_key = ttk.Entry(frame, width=50, show="*")
        self.deepl_key.grid(row=1, column=1, padx=5)

        ttk.Label(frame, text="DeepSeek API Key:").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        self.deepseek_key = ttk.Entry(frame, width=50, show="*")
        self.deepseek_key.grid(row=2, column=1, padx=5)

        ttk.Label(frame, text="Worker Threads:").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        self.threads_entry = ttk.Entry(frame, width=10)
        self.threads_entry.insert(0, "5")
        self.threads_entry.grid(row=3, column=1, sticky='w', padx=5)

        ttk.Button(frame, text="Run Translation", command=self.run_translation).grid(row=4, column=1, pady=15)

        self.log_area = scrolledtext.ScrolledText(self.root, wrap='word', width=100, height=25, state='disabled', font=("Consolas", 10))
        self.log_area.pack(fill='both', expand=True, padx=5, pady=5)

    def setup_logger(self):
        handler = TextHandler(self.log_area)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        # Our app-specific logger
        logger.addHandler(handler)

        # Attach handler to root logger so SDKs and libs emit to GUI
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)  # or DEBUG if needed
        root_logger.addHandler(handler)

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx")])
        if filename:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, filename)

    def run_translation(self):
        thread = threading.Thread(target=self.translate)
        thread.start()

    def translate(self):
        input_file = self.file_entry.get()
        deepl_auth = self.deepl_key.get()
        deepseek_auth = self.deepseek_key.get()
        threads = int(self.threads_entry.get())

        if not all([input_file, deepl_auth, deepseek_auth]):
            messagebox.showerror("Error", "All fields are required.")
            return

        try:
            df = pd.read_excel(input_file)
            df.columns = EXPECTED_COLUMNS
        except Exception as e:
            logger.error(f"Failed to load Excel: {e}")
            return

        df['Model_Requirements'] = df['Model_Requirements'].fillna('N/A')
        df['Scene'] = df['Scene'].fillna('N/A').astype(str)
        df['Pets_Kids'] = df['Pets_Kids'].fillna('N/A').astype(str)
        df['Shooting_Requirements'] = (
            df['Comments'].fillna('').astype(str) + '\n' +
            df['Requirements'].fillna('').astype(str)
        )
        df.drop(columns=['Comments', 'Requirements'], inplace=True)

        try:
            deepl_translator = deepl.Translator(deepl_auth)
        except Exception as e:
            logger.error(f"DeepL initialization failed: {e}")
            return

        for column in ['Product', 'Model_Requirements', 'Scene', 'Pets_Kids']:
            df = translate_column_deepl(df, column, deepl_translator)

        df = translate_column_deepseek(df, 'Shooting_Requirements', api_key=deepseek_auth, max_workers=threads)

        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.strftime('%m/%d/%Y')

        output_file = os.path.splitext(input_file)[0] + "_translated.xlsx"
        try:
            df.to_excel(output_file, index=False)
            logger.info(f"Translation completed. Output saved to: {output_file}")
        except Exception as e:
            logger.error(f"Failed to save output: {e}")

if __name__ == '__main__':
    root = tk.Tk()
    app = TranslatorApp(root)
    root.mainloop()
