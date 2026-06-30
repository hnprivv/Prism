import streamlit as st
import pandas as pd
from analyst import analyse, interpret

st.set_page_config(page_title="Prism", page_icon="🔬", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .main { background-color: #0f0f0f; }

    .hero-title {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #a78bfa, #60a5fa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.25rem;
    }
    .hero-sub {
        color: #9ca3af;
        font-size: 1.05rem;
        margin-bottom: 2rem;
    }
    .schema-box {
        background: #1a1a2e;
        border: 1px solid #2d2d44;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        font-size: 0.82rem;
        color: #a78bfa;
        font-family: monospace;
    }
    .insight-box {
        background: linear-gradient(135deg, #1a1a2e, #0f1729);
        border-left: 3px solid #60a5fa;
        border-radius: 0 10px 10px 0;
        padding: 1rem 1.25rem;
        color: #e2e8f0;
        font-size: 0.95rem;
        line-height: 1.6;
        margin-top: 1.25rem;
    }
    .cannot-box {
        background: #1f1114;
        border-left: 3px solid #f87171;
        border-radius: 0 10px 10px 0;
        padding: 1rem 1.25rem;
        color: #fca5a5;
        font-size: 0.95rem;
        margin-top: 1rem;
    }
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed, #2563eb);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.55rem 1.5rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: opacity 0.2s;
    }
    .stButton > button:hover { opacity: 0.85; }

    [data-testid="stFileUploader"] {
        border: 1.5px dashed #3d3d5c;
        border-radius: 10px;
        padding: 0.5rem;
    }
    .result-panel {
        border: 1.5px dashed #3d3d5c;
        border-radius: 10px;
        padding: 1.25rem;
        min-height: 320px;
    }
</style>
""", unsafe_allow_html=True)

# ── Layout ───────────────────────────────────────────────────────────────────
left, right = st.columns([1, 2], gap="large")

with left:
    st.markdown('<div class="hero-title">Prism</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Upload a spreadsheet. Ask a question. Get an answer.</div>', unsafe_allow_html=True)

    st.markdown("#### Upload your data")
    uploaded = st.file_uploader(
        "CSV or Excel file",
        type=["csv", "xlsx", "xls"],
        label_visibility="collapsed",
    )

    df = None
    if uploaded:
        try:
            if uploaded.name.endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)
            st.success(f"{len(df):,} rows · {len(df.columns)} columns loaded")
        except Exception as e:
            st.error(f"Could not read file: {e}")

    if df is not None:
        with st.expander("Dataset schema", expanded=False):
            schema_lines = []
            for col in df.columns:
                schema_lines.append(f"{col}  ({df[col].dtype})")
            st.markdown(
                '<div class="schema-box">' + "<br>".join(schema_lines) + "</div>",
                unsafe_allow_html=True,
            )

    st.markdown("#### Ask a question")
    question = st.text_area(
        "Question",
        placeholder="e.g. Which city had the highest total sales?",
        height=110,
        label_visibility="collapsed",
        disabled=df is None,
    )

    analyse_btn = st.button("Analyse", disabled=(df is None or not question.strip()))

    if df is None:
        st.caption("Upload a file to get started.")

# ── Analysis ──────────────────────────────────────────────────────────────────
with right:
    st.markdown('<div style="height:23px;"></div>', unsafe_allow_html=True)
    if analyse_btn and df is not None and question.strip():
        with st.spinner("Thinking..."):
            try:
                output = analyse(df, question)
            except Exception as e:
                st.error(f"Analysis failed: {e}")
                st.stop()

        result = output.get("result")
        fig = output.get("fig")

        if result == "CANNOT_ANSWER":
            st.markdown(
                '<div class="cannot-box">This question cannot be answered from the available data. '
                "Try rephrasing or check that the relevant columns exist.</div>",
                unsafe_allow_html=True,
            )
        elif fig is not None:
            fig.update_layout(
                paper_bgcolor="#0f0f0f",
                plot_bgcolor="#1a1a1a",
                font_color="#e2e8f0",
                margin=dict(t=40, b=40, l=60, r=30),
            )
            st.plotly_chart(fig, use_container_width=True)

            with st.spinner("Interpreting result..."):
                insight = interpret(df, question, output)
            if insight:
                st.markdown(
                    f'<div class="insight-box">💡 {insight}</div>',
                    unsafe_allow_html=True,
                )
        elif result is not None:
            if isinstance(result, pd.DataFrame):
                st.dataframe(result, use_container_width=True)
            else:
                st.metric(label=question, value=str(result))

            with st.spinner("Interpreting result..."):
                insight = interpret(df, question, output)
            if insight:
                st.markdown(
                    f'<div class="insight-box">💡 {insight}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.warning("The model returned no output. Try rephrasing your question.")

        sample = output.get("sample")
        if sample is not None and isinstance(sample, pd.DataFrame) and not sample.empty:
            with st.expander("Data sample — verify the logic", expanded=False):
                st.caption("These are the rows behind the answer. Check that the filter/grouping looks correct.")
                st.dataframe(sample, use_container_width=True)

        with st.expander("Generated code", expanded=False):
            st.code(output.get("code", ""), language="python")

    elif not analyse_btn:
        st.markdown(
            """
            <div class="result-panel" style="display:flex; align-items:center; justify-content:center;">
                <span style="color:#4b5563; font-size:0.95rem;">Your chart or table will appear here.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
