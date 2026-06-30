import os
import re
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google import genai

MODEL = "gemini-2.0-flash-lite"

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


def extract_schema(df: pd.DataFrame) -> str:
    lines = ["Column names and types:"]
    for col in df.columns:
        lines.append(f"  - {col} ({df[col].dtype})")
    lines.append("\nFirst 5 rows (as CSV):")
    lines.append(df.head(5).to_csv(index=False))
    return "\n".join(lines)


def _strip_fences(text: str) -> str:
    text = re.sub(r"^```(?:python)?\n?", "", text.strip())
    text = re.sub(r"\n?```$", "", text.strip())
    return text.strip()


def generate_code(schema: str, question: str, error: str = None) -> str:
    error_hint = f"\n\nThe previous attempt failed with this error — fix it:\n{error}" if error else ""

    prompt = f"""You are a data analysis assistant. A pandas DataFrame called `df` is already loaded.

{schema}

User question: {question}{error_hint}

Write Python code that answers the question using `df`.

Rules:
- `df`, `pd`, `px`, and `go` are already available — do NOT import anything.
- For charts: assign a Plotly figure to a variable named `fig`. Add a clear title and axis labels.
- For tables/scalar answers: assign the result to a variable named `result` (a DataFrame or a value).
- Use `fig` for anything visual, `result` for everything else. Never assign both.
- If the question cannot be answered from the available columns, assign: result = "CANNOT_ANSWER"
- Output only raw Python code. No markdown fences. No explanation.
"""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return _strip_fences(response.text)


def run_code(code: str, df: pd.DataFrame) -> dict:
    namespace = {
        "df": df.copy(),
        "pd": pd,
        "px": px,
        "go": go,
    }
    exec(code, namespace)  # noqa: S102
    fig = namespace.get("fig")
    result = namespace.get("result")
    return {"fig": fig, "result": result}


def analyse(df: pd.DataFrame, question: str) -> dict:
    schema = extract_schema(df)
    code = generate_code(schema, question)
    try:
        output = run_code(code, df)
    except Exception as e:
        # one retry with the error fed back
        code = generate_code(schema, question, error=str(e))
        output = run_code(code, df)

    output["code"] = code
    return output


def interpret(df: pd.DataFrame, question: str, output: dict) -> str:
    if output.get("fig"):
        result_description = "A chart was produced."
    elif output.get("result") is not None:
        val = output["result"]
        if isinstance(val, pd.DataFrame):
            result_description = f"A table with {len(val)} rows:\n{val.head(10).to_string(index=False)}"
        else:
            result_description = str(val)
    else:
        return ""

    schema = extract_schema(df)
    prompt = f"""You are a data analyst. A user asked: "{question}"

Dataset schema:
{schema}

Analysis result: {result_description}

Write a single plain-English paragraph (2–4 sentences) interpreting the result for a non-technical reader.
Be specific — mention actual numbers, cities, or categories from the result where possible.
Do not say 'the chart shows' — describe the insight directly."""

    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text.strip()
