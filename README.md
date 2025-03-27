# Excel Translator App with DeepSeek 

A simple desktop GUI application to translate Chinese content in Excel files into English using DeepL and DeepSeek APIs.

## 🖥 Features

- Select any `.xlsx` Excel file
- Enter DeepL and DeepSeek API keys (masked input)
- Set number of parallel threads for DeepSeek translation
- View real-time logs in a scrollable window
- Export translated Excel with `_translated.xlsx` suffix

## ⚙️ Setup Instructions

### 1. Install Dependencies

Make sure you have Python 3.8+ installed. Then run:

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

> You don’t need to set environment variables — just paste the keys directly in the app UI.

## 📁 Project Structure

```
excel_translator_app/
├── main.py          # Entry point to launch the app
├── gui.py           # GUI layout and behavior (Tkinter)
├── translator.py    # Translation logic (DeepL + DeepSeek)
├── logger.py        # Logging setup with GUI integration
├── requirements.txt
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

