import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import threading
import os
import pandas as pd
import deepl
from translator import EXPECTED_COLUMNS, translate_column_deepl, translate_column_deepseek
from logger import setup_gui_logger
from sheets_writer import write_to_google_sheets

class TranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Excel Translator App")
        self.root.geometry("800x600")
        self.root.configure(padx=15, pady=15)

        self.translated_df = None  # Store translated DataFrame for export step
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

        # Google Sheets section (hidden until translation is done)
        self.sheet_id_label = ttk.Label(frame, text="Google Sheet ID:")
        self.sheet_id_entry = ttk.Entry(frame, width=50)

        self.credentials_label = ttk.Label(frame, text="Google Credentials Path:")
        self.credentials_entry = ttk.Entry(frame, width=50)
        self.credentials_browse = ttk.Button(frame, text="Browse", command=self.browse_credentials)

        self.write_button = ttk.Button(frame, text="Write to Google Sheets", command=self.run_write_to_google_sheets)

        self.log_area = scrolledtext.ScrolledText(self.root, wrap='word', width=100, height=25, state='disabled', font=("Consolas", 10))
        self.log_area.pack(fill='both', expand=True, padx=5, pady=5)

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx")])
        if filename:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, filename)

    def browse_credentials(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if filepath:
            self.credentials_entry.delete(0, tk.END)
            self.credentials_entry.insert(0, filepath)

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

        self.translated_df = df  # Store for export step

        # Show Google Sheets inputs and button
        self.sheet_id_label.grid(row=5, column=0, sticky='e', padx=5, pady=5)
        self.sheet_id_entry.grid(row=5, column=1, padx=5)
        self.credentials_label.grid(row=6, column=0, sticky='e', padx=5, pady=5)
        self.credentials_entry.grid(row=6, column=1, padx=5)
        self.credentials_browse.grid(row=6, column=2, padx=5)
        self.write_button.grid(row=7, column=1, pady=15)

    def run_write_to_google_sheets(self):
        sheet_id = self.sheet_id_entry.get()
        credentials_path = self.credentials_entry.get()

        if not sheet_id or not credentials_path:
            messagebox.showerror("Error", "Google Sheets spreadsheet ID and credentials path are required.")
            return

        try:
            unmatched_rows = write_to_google_sheets(self.translated_df, sheet_id, credentials_path, self.logger)

            if unmatched_rows:
                unmatched_df = pd.DataFrame(unmatched_rows)
                output_file = "unmatched_rows.xlsx"
                unmatched_df.to_excel(output_file, index=False)
                self.logger.warning(f"Unmatched rows saved to: {output_file}")

                messagebox.showwarning("Partial Success",
                                       f"{len(unmatched_rows)} row(s) not written. Saved to '{output_file}'.")
                self.show_unmatched_popup(unmatched_df)

            else:
                messagebox.showinfo("Success", "All rows successfully written to Google Sheets.")

        except Exception as e:
            self.logger.error(f"Google Sheets write failed: {e}")
            messagebox.showerror("Error", f"Failed to write to Google Sheets:\n{e}")

    def show_unmatched_popup(self, df):
        window = tk.Toplevel(self.root)
        window.title("Unmatched Rows Viewer")
        window.geometry("1000x400")

        tree = ttk.Treeview(window)
        tree.pack(fill='both', expand=True)

        vsb = ttk.Scrollbar(window, orient="vertical", command=tree.yview)
        vsb.pack(side='right', fill='y')
        tree.configure(yscrollcommand=vsb.set)

        # Setup columns
        tree["columns"] = list(df.columns)
        tree["show"] = "headings"

        for col in df.columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="w", width=150)

        for _, row in df.iterrows():
            tree.insert("", "end", values=list(row))

        ttk.Button(window, text="Close", command=window.destroy).pack(pady=10)
