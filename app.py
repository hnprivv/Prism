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
        background: linear-gradient(135deg, #ef4444, #f97316);
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
    .insight-box {
        background: linear-gradient(135deg, #1a1a2e, #0f1729);
        border-left: 3px solid #f97316;
        border-radius: 0 10px 10px 0;
        padding: 1rem 1.25rem;
        color: #e2e8f0;
        font-size: 0.95rem;
        line-height: 1.6;
        margin-top: 1.25rem;
        margin-bottom: 1.25rem;
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
    .stButton > button,
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #ef4444, #f97316);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.55rem 1.5rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: opacity 0.2s;
    }
    .stButton > button:hover,
    .stFormSubmitButton > button:hover { opacity: 0.85; }

    [data-testid="stForm"] {
        border: none;
        padding: 0;
    }

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

    /* Dialog: header stays put, only content scrolls */
    [data-testid="stDialog"] {
        overflow: hidden !important;
    }
    [data-testid="stDialog"] > div > div > div:nth-child(2) {
        overflow-y: auto;
        max-height: 75vh;
        padding-right: 0.5rem;
    }

    .prism-spinner {
        width: 16px;
        height: 16px;
        border: 2px solid rgba(249, 115, 22, 0.2);
        border-top-color: #f97316;
        border-radius: 50%;
        animation: prism-spin 0.8s linear infinite;
        display: inline-block;
        flex-shrink: 0;
    }
    @keyframes prism-spin { to { transform: rotate(360deg); } }

    [data-testid="stPlotlyChart"] {
        border-radius: 12px;
        box-shadow:
            0 0 60px 8px rgba(239, 68, 68, 0.12),
            0 0 120px 20px rgba(249, 115, 22, 0.07);
    }

    .prism-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 58px;
        box-sizing: border-box;
        text-align: center;
        font-size: 12px;
        color: #484f58;
        padding: 10px 0 12px;
        background: #0e1117;
        border-top: 1px solid #1f1f1f;
        z-index: 999;
    }
    .prism-footer a {
        color: #484f58;
        text-decoration: none;
        transition: color 0.15s;
    }
    .prism-footer a:hover { color: #f97316; }
    .main .block-container { padding-bottom: 70px !important; }

    [data-testid="stHorizontalBlock"] {
        align-items: flex-start;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child {
        position: sticky;
        top: 4.5rem;
    }
    @media (max-width: 768px) {
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child {
            position: static;
        }
    }
</style>
""", unsafe_allow_html=True)

@st.dialog("Dataset Schema")
def show_schema(df):
    for col in df.columns:
        st.markdown(f"`{col}` — *{df[col].dtype}*")


# ── Layout ───────────────────────────────────────────────────────────────────
left, right = st.columns([1, 2], gap="large")

with left:
    st.markdown('<div class="hero-title">Prism</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Upload a spreadsheet. Ask a question. Get an answer.</div>', unsafe_allow_html=True)

    st.markdown("#### Upload File")
    uploaded = st.file_uploader(
        "CSV or Excel file",
        type=["csv", "xlsx", "xls"],
        label_visibility="collapsed",
    )

    df = None
    if uploaded:
        if st.session_state.get("prism_file") != uploaded.name:
            st.session_state.pop("prism_output", None)
            st.session_state.pop("prism_question", None)
            st.session_state.pop("prism_insight", None)
            st.session_state["prism_file"] = uploaded.name
        try:
            if uploaded.name.endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)
            st.success(f"{len(df):,} rows · {len(df.columns)} columns loaded")
        except Exception as e:
            st.error(f"Could not read file: {e}")

    if df is not None:
        if st.button("View Schema", use_container_width=False):
            show_schema(df)

    st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
    st.markdown("#### Input Question")
    with st.form("question_form"):
        question = st.text_area(
            "Question",
            placeholder="e.g. What would the pie chart of sales by category look like?",
            height=110,
            label_visibility="collapsed",
            disabled=df is None,
        )
        analyse_btn = st.form_submit_button(
            "Analyse",
            disabled=df is None,
            use_container_width=False,
        )

    if df is None:
        st.caption("Upload a file to get started.")

    status_slot = st.empty()

# ── Analysis ──────────────────────────────────────────────────────────────────
with right:
    st.markdown('<div style="height:18px;"></div>', unsafe_allow_html=True)
    def _show_status(msg):
        status_slot.markdown(f"""
        <div style="display:flex;align-items:center;gap:0.75rem;
                    background:#161010;border:1px solid #f97316;border-radius:10px;
                    padding:0.75rem 1.25rem;margin-top:0.5rem;">
            <div class="prism-spinner"></div>
            <span style="color:#9ca3af;font-size:0.92rem;font-weight:500;">{msg}</span>
        </div>
        """, unsafe_allow_html=True)

    def _render_results(output, question, insight):
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
            if insight:
                st.markdown(
                    f'<div class="insight-box">💡 {insight}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.warning("The model returned no output. Try rephrasing your question.")

        sample = output.get("sample")
        if sample is not None and isinstance(sample, pd.DataFrame) and not sample.empty:
            with st.expander("Tabular Sample", expanded=False):
                st.caption("These are the rows behind the answer. Check that the filter/grouping looks correct.")
                st.dataframe(sample, use_container_width=True)

        with st.expander("Generated Code", expanded=False):
            st.code(output.get("code", ""), language="python")

    if analyse_btn and df is not None and question.strip():
        _show_status("Analysing your question…")
        try:
            output = analyse(df, question)
        except Exception as e:
            status_slot.empty()
            st.error(f"Analysis failed: {e}")
            st.stop()

        _show_status("Interpreting result…")
        insight = interpret(df, question, output)
        status_slot.empty()

        st.session_state["prism_output"] = output
        st.session_state["prism_question"] = question
        st.session_state["prism_insight"] = insight

        _render_results(output, question, insight)

    elif st.session_state.get("prism_output") is not None:
        _render_results(
            st.session_state["prism_output"],
            st.session_state["prism_question"],
            st.session_state["prism_insight"],
        )

    else:
        st.markdown(
            """
            <div class="result-panel" style="display:flex; align-items:center; justify-content:center;">
                <span style="color:#4b5563; font-size:0.95rem;">Chart will appear here.</span>
            </div>
            <div class="result-panel" style="display:flex; align-items:center; justify-content:center; margin-top:1rem; min-height:300px;">
                <span style="color:#4b5563; font-size:0.95rem;">Table, interpretation and generated code will appear here.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="prism-footer">'
    '© 2026 Prism by <a href="https://github.com/hnprivv">Huzaifa Najam</a>.<br>'
    'Only your dataset schema and question are sent to Google Gemini. '
    'Your data is never uploaded or stored.'
    '</div>',
    unsafe_allow_html=True,
)
