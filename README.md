# Prism

An AI-powered natural language data analyst built with Streamlit and Google Gemini. Upload any spreadsheet and ask questions about it in plain English — Prism inspects the structure, writes the analysis code, executes it, and returns a chart or table with a plain-English interpretation.

No SQL. No formulas. Just ask.

## What it does

- Accepts CSV and Excel files of any size — reads column names, types, and sample rows automatically
- Translates plain-English questions into executable pandas and Plotly code via Google Gemini
- Runs the generated code locally against your data — nothing is sent to the model except the schema and your question
- Returns interactive charts (bar, line, pie, histogram) or tables depending on the question
- Adds a one-paragraph plain-English interpretation of every result
- Exposes the generated code and the underlying data sample so you can verify the logic
- Flags unanswerable questions clearly rather than guessing

## How it works

Prism never asks the model to reason over raw data. Instead it sends the column names, data types, and first five rows to Gemini and asks it to write Python code that answers the question. That code runs locally via `exec()` in a restricted namespace — only `df`, `pd`, `px`, and `go` are available. The result (a Plotly figure or a DataFrame) is then rendered in the UI. If the generated code fails, Prism retries once with the error fed back to the model.

This approach is reliable on large files and keeps prompt costs low regardless of dataset size.

## Tech stack

- **Streamlit** — UI and deployment
- **Google Gemini 2.0 Flash Lite** — code generation and result interpretation
- **google-genai SDK** — Gemini API client
- **pandas** — data loading and manipulation
- **Plotly Express** — interactive chart rendering
- **openpyxl** — Excel file support

## Running locally

```bash
git clone https://github.com/hnprivv/Prism
cd Prism
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

Add your Gemini API key to `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "your-key-here"
```

Get a free key at [aistudio.google.com](https://aistudio.google.com).

```bash
streamlit run app.py
```

## Deploying to Streamlit Cloud

1. Push the repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect the repo
3. Set main file to `app.py`
4. Under Advanced settings → Secrets, add your `GEMINI_API_KEY`
5. Deploy

---

Built by [Huzaifa Najam](https://github.com/hnprivv).
