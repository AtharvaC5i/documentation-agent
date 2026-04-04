"""
app.py  —  AI Solution Architect  ·  Streamlit Frontend
"""

import base64
import json
import os

import requests
import streamlit as st

API_BASE_URL = os.environ.get("ARCHITECT_API_URL", "http://localhost:8000/api/v1")

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="AI Solution Architect",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

    /* ── Reset & Base ── */
    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        background-color: #F7F5FF;
    }

    /* ── Hide Streamlit chrome ── */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container {
        padding: 2.5rem 3rem 4rem 3rem;
        max-width: 1100px;
    }

    /* ── Typography ── */
    h1 {
        font-family: 'DM Serif Display', Georgia, serif !important;
        color: #1B2A5E !important;
        font-size: 2.4rem !important;
        font-weight: 400 !important;
        letter-spacing: -0.5px;
        margin-bottom: 0.1rem !important;
    }
    .subtitle {
        color: #7C5CBF;
        font-size: 1.02rem;
        font-weight: 400;
        margin-bottom: 2.2rem;
        margin-top: -0.3rem;
    }

    /* ── Section labels ── */
    .field-label {
        font-size: 0.78rem;
        font-weight: 600;
        color: #1B2A5E;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.4rem;
    }
    .field-optional {
        font-weight: 400;
        color: #9B93CC;
        text-transform: none;
        letter-spacing: 0;
    }

    /* ── Text areas ── */
    .stTextArea textarea {
        background: #FFFFFF !important;
        border: 1.5px solid #D4CBF0 !important;
        border-radius: 10px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.88rem !important;
        color: #1A1A2E !important;
        padding: 0.75rem 1rem !important;
        transition: border-color 0.2s;
        resize: vertical !important;
        box-shadow: 0 1px 3px rgba(124, 92, 191, 0.07) !important;
    }
    .stTextArea textarea:focus {
        border-color: #7C5CBF !important;
        box-shadow: 0 0 0 3px rgba(124, 92, 191, 0.12) !important;
        outline: none !important;
    }

    /* ── Primary button ── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1B2A5E 0%, #7C5CBF 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 2rem !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.02em !important;
        cursor: pointer !important;
        box-shadow: 0 4px 16px rgba(124, 92, 191, 0.3) !important;
        transition: all 0.2s !important;
        height: 3rem !important;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 24px rgba(124, 92, 191, 0.45) !important;
        transform: translateY(-1px) !important;
    }

    /* ── Secondary button ── */
    .stButton > button[kind="secondary"] {
        background: #FFFFFF !important;
        color: #7C5CBF !important;
        border: 1.5px solid #D4CBF0 !important;
        border-radius: 10px !important;
        padding: 0.75rem 1.5rem !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        height: 3rem !important;
    }
    .stButton > button[kind="secondary"]:hover {
        border-color: #7C5CBF !important;
        background: #F0EBFF !important;
    }

    /* ── Download button ── */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #1A7F5A 0%, #2D9CDB 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        padding: 0.75rem 2rem !important;
        box-shadow: 0 4px 16px rgba(26, 127, 90, 0.25) !important;
        height: 3rem !important;
    }

    /* ── File uploader ── */
    .stFileUploader > div {
        border: 1.5px dashed #D4CBF0 !important;
        border-radius: 10px !important;
        background: #FFFFFF !important;
        padding: 0.5rem !important;
    }

    /* ── Radio button ── */
    .stRadio > div { gap: 0.5rem; }
    .stRadio label {
        font-size: 0.9rem !important;
        color: #1B2A5E !important;
        font-weight: 500 !important;
    }

    /* ── Divider ── */
    hr { border-color: #EDE9F7 !important; margin: 1.8rem 0 !important; }

    /* ── Expander ── */
    .streamlit-expanderHeader {
        font-size: 0.85rem !important;
        color: #7C5CBF !important;
        font-weight: 500 !important;
    }

    /* ── Status messages ── */
    .stSuccess > div {
        background: #F0FDF4 !important;
        border: 1px solid #A7F3D0 !important;
        border-radius: 8px !important;
    }
    .stError > div {
        background: #FFF5F5 !important;
        border: 1px solid #FCA5A5 !important;
        border-radius: 8px !important;
    }
    .stWarning > div {
        background: #FFFBEB !important;
        border: 1px solid #FCD34D !important;
        border-radius: 8px !important;
    }
    .stInfo > div {
        background: #EDE9F7 !important;
        border: 1px solid #D4CBF0 !important;
        border-radius: 8px !important;
        color: #1B2A5E !important;
    }

    /* ── Spinner ── */
    .stSpinner > div > div {
        border-top-color: #7C5CBF !important;
    }

    /* ── Progress card ── */
    .progress-card {
        background: linear-gradient(135deg, #1B2A5E 0%, #2D1B69 100%);
        border-radius: 12px;
        padding: 1.5rem 2rem;
        margin: 1rem 0;
        color: white;
    }
    .progress-card h4 {
        margin: 0 0 0.5rem 0;
        font-family: 'DM Serif Display', serif;
        font-size: 1.1rem;
        font-weight: 400;
    }
    .progress-card p {
        margin: 0;
        font-size: 0.85rem;
        opacity: 0.7;
    }

    /* ── Download banner ── */
    .download-banner {
        background: linear-gradient(135deg, #F0EBFF 0%, #EDE9F7 100%);
        border: 1.5px solid #D4CBF0;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin: 1rem 0;
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    /* ── Input mode toggle ── */
    .stRadio { margin-bottom: 1.2rem; }

    /* ── Caption / hint text ── */
    .stCaption, .caption {
        color: #9B93CC !important;
        font-size: 0.78rem !important;
    }

    /* ── Badge pill ── */
    .badge {
        display: inline-block;
        background: #EDE9F7;
        color: #7C5CBF;
        border-radius: 20px;
        padding: 0.2rem 0.7rem;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.3rem;
    }
    .badge-green { background: #ECFDF5; color: #065F46; }
    .badge-red   { background: #FFF5F5; color: #9B1C1C; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ────────────────────────────────────────────────────
st.markdown("# AI Solution Architect")
st.markdown(
    '<div class="subtitle">Transform your BRD and technical docs into a consulting-quality architecture deck</div>',
    unsafe_allow_html=True,
)

# ── Input mode ────────────────────────────────────────────────
input_mode = st.radio(
    "Input mode",
    ["✏️  Paste text", "📎  Upload files"],
    horizontal=True,
    label_visibility="collapsed",
)

st.markdown("<br>", unsafe_allow_html=True)

# ── Slide selection & custom slides ─────────────────────────────────────
with st.expander("Select slides to include (uncheck to exclude)", expanded=True):
    slides = [
        ("Title", "Title"),
        ("ExecSummary", "Executive Summary"),
        ("Problem", "Problem Statement"),
        ("Solution", "Proposed Solution"),
        ("Diagram", "Architecture Diagram"),
        ("Components", "Component Breakdown"),
        ("DataFlow", "Data Flow"),
        ("TechStack", "Technology Stack"),
        ("Features", "Key Features & Capabilities"),
        ("NFR", "Non-Functional Requirements"),
        ("Roadmap", "Implementation Roadmap"),
        ("Risks", "Risks, Assumptions & Open Questions"),
        ("Closing", "Closing / Next Steps"),
    ]
    selected = []
    cols = st.columns(4)
    for i, (key, label) in enumerate(slides):
        c = cols[i % 4]
        checked = c.checkbox(label, value=True, key=f"slide_{key}")
        if checked:
            selected.append(key)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="field-label">Custom slides (one per line: Title|One-line content)</div>', unsafe_allow_html=True)
    custom_lines = st.text_area("Custom slides", height=80, placeholder="e.g. Appendix|Short note about appendix\nCustom Slide|Single-line content")
    # store for use when generating — always update with latest inputs
    st.session_state["selected_slides"] = selected
    st.session_state["custom_slides_raw"] = custom_lines

brd_text      = ""
tech_doc_text = ""

# ── Text paste mode ───────────────────────────────────────────
if "Paste" in input_mode:
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown('<div class="field-label">Business Requirement Document</div>', unsafe_allow_html=True)
        brd_text = st.text_area(
            "BRD",
            height=240,
            placeholder="Describe the project goal, users, features, constraints…",
            label_visibility="collapsed",
        )

    with col2:
        st.markdown(
            '<div class="field-label">Technical Documentation <span class="field-optional">(optional)</span></div>',
            unsafe_allow_html=True,
        )
        tech_doc_text = st.text_area(
            "Tech Doc",
            height=240,
            placeholder="Existing systems, APIs, data models, infrastructure constraints…",
            label_visibility="collapsed",
        )

# ── File upload mode ──────────────────────────────────────────
else:
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown('<div class="field-label">BRD File</div>', unsafe_allow_html=True)
        st.caption("Supported: .pdf · .docx · .txt · .md")
        brd_file = st.file_uploader(
            "BRD File", type=["pdf", "docx", "txt", "md"],
            label_visibility="collapsed", key="brd_file",
        )
        if brd_file:
            with st.spinner(f"Extracting from {brd_file.name}…"):
                try:
                    resp = requests.post(
                        f"{API_BASE_URL}/extract-text",
                        files={"file": (brd_file.name, brd_file.getvalue(), brd_file.type)},
                        timeout=60,
                    )
                    resp.raise_for_status()
                    result = resp.json()
                    brd_text = result["extracted_text"]
                    if result["warning"]:
                        st.warning(result["warning"])
                    else:
                        st.success(f"✓  {brd_file.name}  —  {result['char_count']:,} characters")
                    with st.expander("Preview extracted text"):
                        st.text(brd_text[:2000] + ("…" if len(brd_text) > 2000 else ""))
                except Exception as e:
                    st.error(f"Extraction failed: {e}")

    with col2:
        st.markdown(
            '<div class="field-label">Technical Documentation <span class="field-optional">(optional)</span></div>',
            unsafe_allow_html=True,
        )
        st.caption("Supported: .pdf · .docx · .txt · .md")
        tech_file = st.file_uploader(
            "Tech Doc File", type=["pdf", "docx", "txt", "md"],
            label_visibility="collapsed", key="tech_file",
        )
        if tech_file:
            with st.spinner(f"Extracting from {tech_file.name}…"):
                try:
                    resp = requests.post(
                        f"{API_BASE_URL}/extract-text",
                        files={"file": (tech_file.name, tech_file.getvalue(), tech_file.type)},
                        timeout=60,
                    )
                    resp.raise_for_status()
                    result = resp.json()
                    tech_doc_text = result["extracted_text"]
                    if result["warning"]:
                        st.warning(result["warning"])
                    else:
                        st.success(f"✓  {tech_file.name}  —  {result['char_count']:,} characters")
                    with st.expander("Preview extracted text"):
                        st.text(tech_doc_text[:2000] + ("…" if len(tech_doc_text) > 2000 else ""))
                except Exception as e:
                    st.error(f"Extraction failed: {e}")

st.markdown("<br>", unsafe_allow_html=True)

# ── Generate button ───────────────────────────────────────────
_, btn_col, _ = st.columns([1, 2, 1])
with btn_col:
    generate = st.button(
        "◈  Generate Architecture Deck",
        type="primary",
        use_container_width=True,
    )

# ── Pipeline execution ────────────────────────────────────────
if generate:
    if not brd_text.strip():
        st.error("Please provide a Business Requirement Document before generating.")
    else:
        with st.spinner(
            "Running AI pipeline: summarising docs → generating architecture → building Mermaid diagram → compiling PowerPoint…"
        ):
            try:
                # Prepare slide selection and custom slides
                sel = st.session_state.get("selected_slides", [])
                raw_cs = st.session_state.get("custom_slides_raw", "") or custom_lines
                resp = requests.post(
                    f"{API_BASE_URL}/generate-pptx",
                    data={
                        "brd_text": brd_text,
                        "tech_doc_text": tech_doc_text,
                        "selected_slides": json.dumps(sel),
                        "custom_slides": raw_cs,
                    },
                    timeout=360,
                )
                resp.raise_for_status()
                st.session_state["pptx_bytes"] = resp.content
                st.success("Architecture deck generated successfully.")
            except requests.exceptions.Timeout:
                st.error(
                    "The pipeline timed out. This can happen with very long documents. "
                    "Try shortening your BRD or tech doc, then try again."
                )
            except requests.exceptions.HTTPError as e:
                detail = ""
                try:
                    detail = e.response.json().get("detail", e.response.text[:300])
                except Exception:
                    detail = e.response.text[:300]
                st.error(f"Pipeline error ({e.response.status_code}): {detail}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")

# ── Download section ──────────────────────────────────────────
if "pptx_bytes" in st.session_state:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg,#EDE9F7,#F7F5FF);
            border: 1.5px solid #D4CBF0;
            border-radius: 12px;
            padding: 1.2rem 1.5rem 0.6rem 1.5rem;
            margin-bottom: 1rem;
        ">
            <div style="font-family:'DM Serif Display',serif; font-size:1.15rem; color:#1B2A5E; margin-bottom:0.35rem;">
                Your deck is ready
            </div>
            <div style="font-size:0.85rem; color:#7C5CBF;">
                13-slide consulting-quality architecture document · Mermaid diagram embedded · Ready to present
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, dl_col, _ = st.columns([1, 2, 1])
    with dl_col:
        st.download_button(
            label="⬇  Download architecture.pptx",
            data=st.session_state["pptx_bytes"],
            file_name="architecture.pptx",
            mime=(
                "application/vnd.openxmlformats-officedocument"
                ".presentationml.presentation"
            ),
            use_container_width=True,
        )

    st.markdown(
        "<div style='text-align:center; color:#9B93CC; font-size:0.8rem; margin-top:0.5rem;'>"
        "Want a fresh deck without re-running the AI? Use the button below."
        "</div>",
        unsafe_allow_html=True,
    )

# ── Footer hint ───────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center; color:#C4BAE8; font-size:0.77rem;'>"
    "Powered by Databricks · Claude Sonnet · mermaid.ink"
    "</div>",
    unsafe_allow_html=True,
)