import re
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from google import genai

MODEL = "gemini-3.1-flash-lite"

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])


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
- Default to a chart. Produce a chart (assign a Plotly figure to `fig`) whenever the question involves any of:
  comparing categories, a trend over time, a distribution, a ranking/top-N, a breakdown/grouping, or a share of total.
  Pick the right chart type: bar for category comparisons, line for time trends, pie/donut for share-of-total, histogram for distributions.
  Add a clear title and axis labels.
- Only assign `result` (no `fig`) when the question asks for a single direct number/value (e.g. "how many rows", "what is the average X") with no natural category/time breakdown, or when the question explicitly asks to "list" or "show the rows".
- Never assign both `fig` and `result`.
- If the question cannot be answered from the available columns, assign: result = "CANNOT_ANSWER"
- Always assign a variable named `sample`: the intermediate DataFrame that produced the answer (e.g. the filtered or grouped rows before aggregation). Limit it to 10 rows with .head(10). For chart questions, this is the data passed to px. For scalar questions, this is the filtered df. Skip only if result = "CANNOT_ANSWER".
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
    sample = namespace.get("sample")
    return {"fig": fig, "result": result, "sample": sample}


def analyse(df: pd.DataFrame, question: str) -> dict:
    schema = extract_schema(df)

    t0 = time.perf_counter()
    code = generate_code(schema, question)
    t_codegen = time.perf_counter() - t0

    retried = False
    t1 = time.perf_counter()
    try:
        output = run_code(code, df)
    except Exception as e:
        retried = True
        code = generate_code(schema, question, error=str(e))
        output = run_code(code, df)
    t_exec = time.perf_counter() - t1

    output["code"] = code
    output["metrics"] = {
        "codegen_s": round(t_codegen, 2),
        "exec_s": round(t_exec, 3),
        "total_s": round(t_codegen + t_exec, 2),
        "retried": retried,
    }
    return output


def interpret(df: pd.DataFrame, question: str, output: dict) -> str:
    sample = output.get("sample")
    sample_text = (
        f"\nUnderlying data used to produce this result:\n{sample.to_string(index=False)}"
        if sample is not None and isinstance(sample, pd.DataFrame) and not sample.empty
        else ""
    )

    if output.get("fig"):
        result_description = f"A chart was produced.{sample_text}"
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
