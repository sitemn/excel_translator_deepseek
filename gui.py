import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import threading
import os
import pandas as pd
import deepl
from translator import EXPECTED_COLUMNS, translate_column_deepl, translate_column_deepseek
from logger import setup_gui_logger

class TranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Excel Translator App")
        self.root.geometry("800x600")
        self.root.configure(padx=15, pady=15)

        self.create_widgets()
        self.logger = setup_gui_logger(self.log_area)

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
            self.logger.error(f"Failed to load Excel: {e}")
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
            self.logger.error(f"DeepL initialization failed: {e}")
            return

        for column in ['Product', 'Model_Requirements', 'Scene', 'Pets_Kids']:
            df = translate_column_deepl(df, column, deepl_translator)

        df = translate_column_deepseek(df, 'Shooting_Requirements', api_key=deepseek_auth, max_workers=threads)

        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.strftime('%m/%d/%Y')

        output_file = os.path.splitext(input_file)[0] + "_translated.xlsx"
        try:
            df.to_excel(output_file, index=False)
            self.logger.info(f"Translation completed. Output saved to: {output_file}")
        except Exception as e:
            self.logger.error(f"Failed to save output: {e}")
