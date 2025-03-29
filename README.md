# Excel Translator App Using DeepSeek And Deepl with Google Sheets Export

This app is a GUI-based tool built with Python and Tkinter that allows you to:
- 📥 Translate columns in an Excel file from Chinese to English using **DeepL** and **DeepSeek** APIs.
- 📤 Write the translated data to specific worksheets in a Google Sheets document using address-based matching.
- 📁 Export unmatched rows (with no corresponding worksheet) to a separate Excel file and view them in a popup.

## 🖥 Features
✅ Translate Excel files using:
- **DeepL API** for columns like `Product`, `Model_Requirements`, `Scene`, `Pets_Kids`
- **DeepSeek API** for `Shooting_Requirements` (combined from `Comments` + `Requirements`)
- Select any `.xlsx` Excel file
- Enter DeepL and DeepSeek API keys (masked input)
- Set number of parallel threads for DeepSeek translation
- View real-time logs in a scrollable window
- Export translated Excel with `_translated.xlsx` suffix

✅ Google Sheets integration:
- Use the `Address` number to match the correct worksheet tab
- Append translated data to the matched worksheet
- Save unmatched rows to `unmatched_rows.xlsx`
- View unmatched rows in a GUI window for review

## ⚙️ Setup Instructions

### 1. Install Dependencies

Make sure you have Python 3.8+ installed.

Install required packages:

```bash
pip install -r requirements.txt
```

### 2. Get Your API Keys

#### 🔑 DeepL API Key
- Sign up at [https://www.deepl.com/pro](https://www.deepl.com/pro)
- Go to your [DeepL Account page](https://www.deepl.com/account)
- Copy your **Authentication Key**

#### 🔑 DeepSeek API Key
- Visit [https://platform.deepseek.com](https://platform.deepseek.com)
- Sign up or log in
- Navigate to your **API Keys** section
- Copy the key for use in the app

### 3. Google Sheets Setup

#### a. Enable Sheets API
- Create a project at Google Cloud Console

- Enable Google Sheets API

#### b. Create Service Account
- Create a service account and download the JSON credentials

- Share your target Google Sheet with the service account email

## 📁 Project Structure

```
excel_translator_app/
├── gui.py                 # Main GUI code
├── main.py                # Entry point
├── translator.py          # Translation logic (DeepL, DeepSeek)
├── logger.py              # Logging to GUI
├── sheets_writer.py       # Google Sheets logic
├── gspread_helper.py      # Auth & append helpers
├── unmatched_rows.xlsx    # Output for skipped rows
├── requirements.txt
└── README.md
```

## 🚀 How to Run

1. Launch the app:
    ```bash
    python main.py
    ```

2. Follow the UI:
    - Select Excel file
    - Paste both API keys
    - Set thread count (optional)
    - Click **Run Translation**

## 📦 Requirements

- Python 3.8+
- Required packages listed in `requirements.txt`

## 📝 Notes

- Ensure `openpyxl` is installed for Excel file support.
- Translations are saved as `<your_file>_translated.xlsx` in the same folder.
- Logs appear live in the application window.

## 📃 License

MIT License


## 📄 Expected Excel Header Format

Your Excel file must include the following columns :

```text
['Date', 'Address', 'Product', 'ASIN', 'Model_Requirements', 'Total_Video', 'Scene', 'Pets_Kids', 'Requirements', 'Comments']
```

