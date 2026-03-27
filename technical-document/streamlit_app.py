import streamlit as st
import requests
import json
import time

st.set_page_config(page_title="DocAgent", layout="wide", initial_sidebar_state="collapsed")

API_BASE = "http://localhost:8000"

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
  background: #f5f5f3 !important;
  color: #1a1a18 !important;
}

#MainMenu, footer, header, [data-testid="stSidebar"] { display: none !important; }

.block-container {
  padding: 0 2rem 5rem 2rem !important;
  max-width: 1100px !important;
  margin: 0 auto !important;
}

/* ── Topbar ── */
.topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 1rem 0; margin-bottom: 1.5rem;
  border-bottom: 1px solid #e2e2de;
}
.brand {
  display: flex; align-items: center; gap: 0.5rem;
  font-size: 0.95rem; font-weight: 700; color: #111;
  letter-spacing: -0.02em;
}
.brand-dot { color: #2563eb; }
.api-pill {
  font-size: 0.65rem; font-weight: 600; padding: 0.2rem 0.6rem;
  border-radius: 20px; letter-spacing: 0.04em;
}
.api-on  { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
.api-off { background: #fee2e2; color: #dc2626; border: 1px solid #fecaca; }

/* ── Stepper ── */
.stepper {
  display: flex; align-items: center; gap: 0;
  background: #fff; border: 1px solid #e2e2de;
  border-radius: 10px; padding: 0; margin-bottom: 2rem;
  overflow: hidden;
}
.step-item {
  flex: 1; display: flex; align-items: center; justify-content: center;
  gap: 0.45rem; padding: 0.65rem 0.5rem; cursor: pointer;
  font-size: 0.72rem; font-weight: 500; color: #9ca3af;
  border-right: 1px solid #f0f0ee; transition: all 0.15s;
  white-space: nowrap;
}
.step-item:last-child { border-right: none; }
.step-item.active { background: #2563eb; color: #fff; font-weight: 600; }
.step-item.done { background: #f0fdf4; color: #15803d; }
.step-num {
  width: 18px; height: 18px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.6rem; font-weight: 700; flex-shrink: 0;
  background: rgba(0,0,0,0.06);
}
.step-item.active .step-num { background: rgba(255,255,255,0.25); }
.step-item.done .step-num { background: #bbf7d0; color: #15803d; }

/* ── Page header ── */
.ph { margin-bottom: 1.5rem; }
.ph-title {
  font-size: 1.2rem; font-weight: 700; color: #111;
  letter-spacing: -0.025em; margin-bottom: 0.3rem;
}
.ph-sub { font-size: 0.8rem; color: #6b7280; line-height: 1.6; max-width: 580px; }

/* ── Cards ── */
.card {
  background: #fff; border: 1px solid #e2e2de;
  border-radius: 10px; padding: 1.2rem 1.4rem; margin-bottom: 0.75rem;
}
.card-blue {
  background: #eff6ff; border: 1px solid #bfdbfe;
  border-radius: 10px; padding: 1.1rem 1.3rem; margin-bottom: 0.75rem;
}
.card-green {
  background: #f0fdf4; border: 1px solid #bbf7d0;
  border-radius: 10px; padding: 1.1rem 1.3rem; margin-bottom: 0.75rem;
}
.card-amber {
  background: #fffbeb; border: 1px solid #fde68a;
  border-radius: 10px; padding: 1.1rem 1.3rem; margin-bottom: 0.75rem;
}
.card-red {
  background: #fff5f5; border: 1px solid #fecaca;
  border-radius: 10px; padding: 1.1rem 1.3rem; margin-bottom: 0.75rem;
}

/* ── Metric card ── */
.mc { background: #fff; border: 1px solid #e2e2de; border-radius: 10px; padding: 1rem 1.2rem; }
.mc-label { font-size: 0.6rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #9ca3af; margin-bottom: 0.3rem; }
.mc-val { font-size: 1.55rem; font-weight: 700; color: #111; letter-spacing: -0.04em; line-height: 1; }
.mc-sub { font-size: 0.67rem; color: #9ca3af; margin-top: 0.15rem; }

/* ── Section label ── */
.slabel {
  font-size: 0.6rem; font-weight: 700; letter-spacing: 0.12em;
  text-transform: uppercase; color: #9ca3af;
  display: flex; align-items: center; gap: 0.5rem;
  margin: 1.25rem 0 0.65rem 0;
}
.slabel::after { content: ""; flex: 1; height: 1px; background: #e2e2de; }

/* ── Badges ── */
.badge {
  display: inline-flex; align-items: center; gap: 0.25rem;
  padding: 0.18rem 0.55rem; border-radius: 4px;
  font-size: 0.62rem; font-weight: 600; letter-spacing: 0.04em;
  text-transform: uppercase;
}
.b-green  { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
.b-red    { background: #fee2e2; color: #dc2626; border: 1px solid #fecaca; }
.b-blue   { background: #dbeafe; color: #1d4ed8; border: 1px solid #bfdbfe; }
.b-amber  { background: #fef9c3; color: #854d0e; border: 1px solid #fde68a; }
.b-gray   { background: #f3f4f6; color: #6b7280; border: 1px solid #e5e7eb; }

/* ── Notice ── */
.notice {
  display: flex; gap: 0.7rem; align-items: flex-start;
  padding: 0.8rem 1rem; border-radius: 8px;
  font-size: 0.78rem; line-height: 1.65; margin-bottom: 1rem;
}
.n-info  { background: #eff6ff; border: 1px solid #bfdbfe; color: #1d4ed8; }
.n-ok    { background: #f0fdf4; border: 1px solid #bbf7d0; color: #15803d; }
.n-warn  { background: #fffbeb; border: 1px solid #fde68a; color: #92400e; }
.n-error { background: #fff5f5; border: 1px solid #fecaca; color: #b91c1c; }

/* ── Tag ── */
.tag {
  display: inline-block; background: #f3f4f6; border: 1px solid #e5e7eb;
  color: #374151; border-radius: 4px; padding: 0.12rem 0.45rem;
  font-size: 0.67rem; font-family: 'SF Mono', 'Fira Code', monospace; margin: 0.1rem;
}

/* ── Section row (review) ── */
.srow {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 0.3rem; border: 1px solid;
}
.srow-pending  { background: #fafafa;  border-color: #e5e7eb; }
.srow-approved { background: #f0fdf4;  border-color: #bbf7d0; }
.srow-rejected { background: #fff5f5;  border-color: #fecaca; }

/* ── Reorder row ── */
.reorder-row {
  display: flex; align-items: center; gap: 0.75rem;
  background: #fff; border: 1px solid #e2e2de; border-radius: 8px;
  padding: 0.65rem 1rem; margin-bottom: 0.3rem;
  font-size: 0.82rem; color: #374151; font-weight: 500;
}
.reorder-num {
  width: 24px; height: 24px; border-radius: 6px; background: #eff6ff;
  border: 1px solid #bfdbfe; color: #1d4ed8;
  font-size: 0.62rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}

/* ── Divider ── */
.hr { border: none; border-top: 1px solid #f0f0ee; margin: 1.25rem 0; }

/* ── Streamlit overrides ── */
.stTextInput label, .stTextArea label, .stFileUploader label, .stSelectbox label {
  font-size: 0.62rem !important; font-weight: 700 !important;
  letter-spacing: 0.1em !important; text-transform: uppercase !important; color: #9ca3af !important;
}
.stTextInput input, .stSelectbox select {
  background: #fff !important; border: 1px solid #e2e2de !important;
  border-radius: 7px !important; font-size: 0.83rem !important;
}
.stTextArea textarea {
  background: #fff !important; border: 1px solid #e2e2de !important;
  border-radius: 7px !important; font-size: 0.83rem !important;
}
.stButton > button {
  background: #2563eb !important; border: 1px solid #2563eb !important;
  color: #fff !important; border-radius: 7px !important;
  font-size: 0.78rem !important; font-weight: 600 !important;
  padding: 0.48rem 1.2rem !important;
}
.stButton > button:hover { background: #1d4ed8 !important; border-color: #1d4ed8 !important; }
.stButton > button[kind="secondary"] {
  background: #fff !important; border: 1px solid #e2e2de !important;
  color: #374151 !important;
}
.stProgress > div > div { background: #2563eb !important; border-radius: 3px !important; }
[data-testid="stFileUploadDropzone"] {
  background: #fff !important; border: 1.5px dashed #d1d5db !important; border-radius: 8px !important;
}
[data-testid="stTabs"] button[role="tab"] {
  font-size: 0.75rem !important; font-weight: 500 !important; color: #6b7280 !important;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
  color: #2563eb !important; border-bottom: 2px solid #2563eb !important; font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
DEFAULTS = {
    "page": 0,
    "project_id": None,
    "analysis": None,
    "metadata": {},
    "suggestions": [],
    "confirmed_sections": [],      # list[str]
    "context_result": None,
    "generation_results": [],      # list[dict] — raw from API
    "generation_started": False,
    "generation_finished": False,
    "section_order": [],           # list[str] — user-arranged order for assembly
    "review_decisions": {},        # {section_name: {"action": ..., "edited_content": ...}}
    "assembly_result": None,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def api_call(method, endpoint, **kwargs):
    try:
        r = getattr(requests, method)(f"{API_BASE}{endpoint}", timeout=180, **kwargs)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "connection_error"
    except requests.exceptions.HTTPError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, detail
    except Exception as e:
        return None, str(e)

def api_online():
    d, _ = api_call("get", "/health")
    return d is not None

def go(i):
    st.session_state.page = i

def notice(msg, kind="info"):
    icons = {"info": "ℹ", "ok": "✓", "warn": "⚠", "error": "✕"}
    cls = {"info": "n-info", "ok": "n-ok", "warn": "n-warn", "error": "n-error"}
    st.markdown(
        f'<div class="notice {cls[kind]}">'
        f'<span style="font-weight:700;flex-shrink:0">{icons[kind]}</span>'
        f'<span>{msg}</span></div>',
        unsafe_allow_html=True,
    )

def slabel(text):
    st.markdown(f'<div class="slabel">{text}</div>', unsafe_allow_html=True)

def hr():
    st.markdown('<hr class="hr">', unsafe_allow_html=True)

def mc(label, val, sub=""):
    s = f'<div class="mc-sub">{sub}</div>' if sub else ""
    st.markdown(
        f'<div class="mc"><div class="mc-label">{label}</div>'
        f'<div class="mc-val">{val}</div>{s}</div>',
        unsafe_allow_html=True,
    )

def tag_row(items):
    st.markdown("".join(f'<span class="tag">{i}</span>' for i in (items or [])), unsafe_allow_html=True)

def get_gen_sections():
    """Return generation results as a normalised list of dicts with 'name', 'content', 'order', 'quality_score'."""
    raw = st.session_state.get("generation_results", [])
    out = []
    for s in raw:
        out.append({
            "name":          s.get("name") or s.get("section_name", ""),
            "content":       s.get("content", ""),
            "order":         s.get("order", 0),
            "quality_score": s.get("quality_score", 0.0),
            "status":        s.get("status", "success"),
            "regenerated":   s.get("regenerated", False),
        })
    return out

# ─────────────────────────────────────────────────────────────────────────────
# TOPBAR
# ─────────────────────────────────────────────────────────────────────────────
online = api_online()
status_pill = (
    '<span class="api-pill api-on">● API Live</span>' if online
    else '<span class="api-pill api-off">● API Offline</span>'
)
pname_display = st.session_state.metadata.get("project_name", "")
pid_short = (st.session_state.project_id or "")[:8]
crumb = (
    f'<span style="font-size:0.72rem;color:#9ca3af;margin-left:1rem">'
    f'/ {pname_display} <span style="font-family:monospace;font-size:0.62rem;color:#d1d5db">{pid_short}</span>'
    f'</span>'
    if st.session_state.project_id else ""
)
st.markdown(
    f'<div class="topbar">'
    f'<div class="brand">&#9632; Doc<span class="brand-dot">Agent</span>{crumb}</div>'
    f'{status_pill}</div>',
    unsafe_allow_html=True,
)

if not online:
    notice("API server not responding. Start with <code>python run.py</code> then refresh.", "error")

# ─────────────────────────────────────────────────────────────────────────────
# STEPPER
# ─────────────────────────────────────────────────────────────────────────────
STEPS = [
    (0, "Ingest"),
    (1, "Sections"),
    (2, "Context"),
    (3, "Generate"),
    (4, "Review"),
    (5, "Assemble"),
]
DONE_FLAGS = [
    bool(st.session_state.analysis),
    bool(st.session_state.confirmed_sections),
    bool(st.session_state.context_result),
    bool(st.session_state.generation_finished),
    bool(st.session_state.review_decisions),
    bool(st.session_state.assembly_result),
]
cur = st.session_state.page
step_html = '<div class="stepper">'
for idx, (num, lbl) in enumerate(STEPS):
    cls = "active" if idx == cur else ("done" if DONE_FLAGS[idx] else "")
    num_inner = "✓" if (DONE_FLAGS[idx] and idx != cur) else str(num + 1)
    step_html += (
        f'<div class="step-item {cls}" onclick="">'
        f'<span class="step-num">{num_inner}</span>{lbl}</div>'
    )
step_html += "</div>"
st.markdown(step_html, unsafe_allow_html=True)

# Navigation buttons (hidden but functional)
nav_cols = st.columns(len(STEPS))
for i, (col, (num, lbl)) in enumerate(zip(nav_cols, STEPS)):
    with col:
        if st.button(lbl, key=f"nav_{i}", use_container_width=True):
            go(i); st.rerun()

st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# STEP 0 — INGEST
# ═════════════════════════════════════════════════════════════════════════════
if cur == 0:
    left, right = st.columns([6, 5], gap="large")

    with left:
        st.markdown(
            '<div class="ph"><div class="ph-title">Ingest Codebase</div>'
            '<div class="ph-sub">Provide a GitHub repository or a ZIP archive. '
            'Binaries, lock files, and node_modules are stripped automatically.</div></div>',
            unsafe_allow_html=True,
        )

        gh_tab, zip_tab = st.tabs(["GitHub Repository", "ZIP Archive"])

        with gh_tab:
            c1, c2 = st.columns(2)
            with c1:
                gh_url   = st.text_input("Repository URL", placeholder="https://github.com/owner/repo")
                gh_token = st.text_input("Access Token", type="password", placeholder="ghp_... (optional)")
            with c2:
                gh_name   = st.text_input("Project Name", placeholder="My API Service")
                gh_client = st.text_input("Client", placeholder="Acme Corp")
                gh_team   = st.text_input("Team", placeholder="Alice, Bob")
                gh_desc   = st.text_area("Description", height=68, placeholder="What does this project do?")
            hr()
            if online and st.button("Clone & Analyse", key="btn_gh", use_container_width=True):
                if not gh_url.strip() or not gh_name.strip() or not gh_client.strip():
                    st.error("URL, project name and client are required.")
                else:
                    bar = st.progress(0, text="Connecting…")
                    for p, msg in [(15,"Cloning…"),(40,"Filtering…"),(70,"Analysing stack…"),(90,"Finalising…")]:
                        time.sleep(0.3); bar.progress(p, text=msg)
                    payload = {
                        "source_type": "github", "github_url": gh_url.strip(),
                        "github_token": gh_token.strip() or None,
                        "metadata": {
                            "project_name": gh_name.strip(), "client_name": gh_client.strip(),
                            "team_members": [m.strip() for m in gh_team.split(",") if m.strip()],
                            "description": gh_desc.strip(),
                        },
                    }
                    data, err = api_call("post", "/ingest/github", json=payload)
                    bar.progress(100, text="Done.")
                    if err:
                        notice(f"Ingestion failed: {err}", "error")
                    else:
                        st.session_state.update(
                            project_id=data["project_id"], analysis=data["analysis"],
                            metadata=payload["metadata"],
                        )
                        st.rerun()

        with zip_tab:
            c1, c2 = st.columns(2)
            with c1:
                z_file = st.file_uploader("ZIP File", type="zip")
            with c2:
                z_name   = st.text_input("Project Name ", placeholder="My Project")
                z_client = st.text_input("Client ", placeholder="Acme Corp")
                z_team   = st.text_input("Team ", placeholder="Alice, Bob")
                z_desc   = st.text_area("Description ", height=68, placeholder="What does this project do?")
            hr()
            if online and st.button("Extract & Analyse", key="btn_zip", use_container_width=True):
                if not z_file or not z_name.strip() or not z_client.strip():
                    st.error("ZIP file, project name and client are required.")
                else:
                    bar = st.progress(0, text="Reading…")
                    for p, msg in [(20,"Extracting…"),(50,"Filtering…"),(80,"Analysing…")]:
                        time.sleep(0.3); bar.progress(p, text=msg)
                    data, err = api_call("post", "/ingest/zip",
                        files={"file": (z_file.name, z_file.getvalue(), "application/zip")},
                        data={
                            "project_name": z_name.strip(), "client_name": z_client.strip(),
                            "team_members": json.dumps([m.strip() for m in z_team.split(",") if m.strip()]),
                            "description": z_desc.strip(),
                        },
                    )
                    bar.progress(100, text="Done.")
                    if err:
                        notice(f"Extraction failed: {err}", "error")
                    else:
                        st.session_state.update(
                            project_id=data["project_id"], analysis=data["analysis"],
                            metadata={"project_name": z_name, "client_name": z_client,
                                      "team_members": [m.strip() for m in z_team.split(",") if m.strip()],
                                      "description": z_desc},
                        )
                        st.rerun()

        if st.session_state.analysis:
            a = st.session_state.analysis
            hr()
            notice("Codebase ingested and analysed successfully.", "ok")
            m = st.columns(4)
            with m[0]: mc("Lines of Code", f"{a.get('total_loc',0):,}", "source LOC")
            with m[1]: mc("Endpoints",     str(a.get("api_endpoints_count", 0)), "detected")
            with m[2]: mc("Strategy",      "RAPTOR" if a.get("total_loc",0) > 50000 else "Flat")
            with m[3]: mc("Files",         str(a.get("filtered_file_count", 0)), "after filter")
            st.markdown('<div style="height:0.75rem"></div>', unsafe_allow_html=True)
            for key, lbl in [("languages","Languages"),("frameworks","Frameworks"),("databases","Databases")]:
                if a.get(key):
                    slabel(lbl); tag_row(a[key])
            st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
            if st.button("Continue to Sections →", use_container_width=True):
                go(1); st.rerun()

    with right:
        st.markdown('<div style="height:4rem"></div>', unsafe_allow_html=True)
        slabel("How DocAgent works")
        steps_info = [
            ("1", "Ingest", "Clone or upload code. Noise stripped automatically."),
            ("2", "Sections", "AI suggests docs sections based on your actual stack."),
            ("3", "Context", "Code embedded locally in ChromaDB — nothing leaves your machine."),
            ("4", "Generate", "Each section written via RAG. Low-quality sections auto-regenerated."),
            ("5", "Review", "Approve, edit, reject, reorder sections before assembly."),
            ("6", "Assemble", "Download as .docx / .pdf or send by email."),
        ]
        for num, title, desc in steps_info:
            st.markdown(
                f'<div style="display:flex;gap:0.75rem;padding:0.65rem 0;border-bottom:1px solid #f0f0ee">'
                f'<div style="width:20px;height:20px;border-radius:5px;background:#eff6ff;border:1px solid #bfdbfe;'
                f'color:#2563eb;font-size:0.6rem;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0">{num}</div>'
                f'<div><div style="font-size:0.78rem;font-weight:600;color:#374151;margin-bottom:0.1rem">{title}</div>'
                f'<div style="font-size:0.7rem;color:#9ca3af;line-height:1.55">{desc}</div></div></div>',
                unsafe_allow_html=True,
            )
        if st.session_state.project_id:
            st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
            slabel("Active project")
            st.markdown(
                f'<div class="card-blue">'
                f'<div style="font-size:0.85rem;font-weight:600;color:#1d4ed8">'
                f'{st.session_state.metadata.get("project_name","")}</div>'
                f'<div style="font-size:0.7rem;color:#6b8af0;margin-top:0.2rem">'
                f'Client: {st.session_state.metadata.get("client_name","")}</div>'
                f'<div style="font-family:monospace;font-size:0.58rem;color:#93c5fd;margin-top:0.4rem">'
                f'{st.session_state.project_id}</div></div>',
                unsafe_allow_html=True,
            )
            if st.button("New Project", use_container_width=True, key="reset_0"):
                for k, v in DEFAULTS.items(): st.session_state[k] = v
                st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# STEP 1 — SECTIONS
# ═════════════════════════════════════════════════════════════════════════════
elif cur == 1:
    if not st.session_state.project_id:
        notice("Complete Step 1 (Ingest) first.", "error")
        if st.button("← Back to Ingest"): go(0); st.rerun()
        st.stop()

    left, right = st.columns([6, 5], gap="large")

    with left:
        st.markdown(
            '<div class="ph"><div class="ph-title">Section Selection</div>'
            '<div class="ph-sub">AI reviews your stack and recommends documentation sections. '
            'Adjust the selection and add custom sections as needed.</div></div>',
            unsafe_allow_html=True,
        )

        if st.button("Generate Suggestions", use_container_width=True, key="load_sugg"):
            with st.spinner("Analysing stack…"):
                data, err = api_call("get", f"/sections/suggest/{st.session_state.project_id}")
            if err:
                notice(f"Failed: {err}", "error")
            else:
                st.session_state.suggestions = data["suggestions"]; st.rerun()

        if st.session_state.suggestions:
            suggs = st.session_state.suggestions
            rec = [s for s in suggs if s["selected"]]
            opt = [s for s in suggs if not s["selected"]]
            chosen = []

            if rec:
                slabel(f"Recommended — {len(rec)} sections")
                for s in rec:
                    checked = st.checkbox(s["name"], value=True, key=f"cs_{s['name']}")
                    st.markdown(
                        f'<div style="font-size:0.69rem;color:#6b7280;margin:-0.4rem 0 0.6rem 1.65rem">{s["reason"]}</div>',
                        unsafe_allow_html=True,
                    )
                    if checked: chosen.append(s["name"])

            if opt:
                slabel(f"Optional — {len(opt)} sections")
                for s in opt:
                    checked = st.checkbox(s["name"], value=False, key=f"cs_{s['name']}")
                    st.markdown(
                        f'<div style="font-size:0.69rem;color:#9ca3af;margin:-0.4rem 0 0.6rem 1.65rem">{s["reason"]}</div>',
                        unsafe_allow_html=True,
                    )
                    if checked: chosen.append(s["name"])

            hr()
            slabel("Custom sections")
            custom_raw = st.text_input(
                "Comma-separated titles", placeholder="GDPR Compliance, Data Migration Guide",
                label_visibility="collapsed",
            )
            custom = [c.strip() for c in custom_raw.split(",") if c.strip()]
            all_sec = chosen + custom

            if all_sec:
                slabel(f"Queued — {len(all_sec)} sections")
                st.markdown(
                    "".join(
                        f'<span style="display:inline-flex;align-items:center;background:#dbeafe;'
                        f'border:1px solid #bfdbfe;color:#1d4ed8;border-radius:4px;padding:0.2rem 0.55rem;'
                        f'font-size:0.7rem;font-weight:500;margin:0.15rem">{s}</span>'
                        for s in all_sec
                    ),
                    unsafe_allow_html=True,
                )

            hr()
            if st.button("Confirm & Continue →", use_container_width=True, key="confirm_sec"):
                if not all_sec:
                    st.error("Select at least one section.")
                else:
                    with st.spinner("Saving…"):
                        data, err = api_call("post", "/sections/confirm", json={
                            "project_id": st.session_state.project_id,
                            "confirmed_sections": chosen,
                            "custom_sections": custom,
                        })
                    if err:
                        st.error(f"Failed: {err}")
                    else:
                        st.session_state.confirmed_sections = data["final_sections"]
                        st.session_state.section_order = data["final_sections"][:]
                        go(2); st.rerun()
        else:
            notice("Click <b>Generate Suggestions</b> to get AI-driven recommendations.", "info")

    with right:
        if st.session_state.analysis:
            a = st.session_state.analysis
            st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)
            slabel("Stack detected")
            for key, lbl in [("languages","Languages"),("frameworks","Frameworks"),("databases","Databases")]:
                if a.get(key):
                    st.markdown(f'<div style="font-size:0.62rem;font-weight:700;color:#9ca3af;margin:0.6rem 0 0.3rem;text-transform:uppercase;letter-spacing:0.08em">{lbl}</div>', unsafe_allow_html=True)
                    tag_row(a[key])
            st.markdown('<div style="height:0.75rem"></div>', unsafe_allow_html=True)
            flags = [("has_dockerfile","Dockerfile"),("has_cicd","CI/CD"),("has_kubernetes","Kubernetes"),("has_terraform","Terraform")]
            for k, lbl in flags:
                val = a.get(k, False)
                color = "#15803d" if val else "#d1d5db"
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:0.5rem;font-size:0.73rem;'
                    f'color:{"#374151" if val else "#9ca3af"};margin-bottom:0.25rem">'
                    f'<span style="width:8px;height:8px;border-radius:50%;background:{color};flex-shrink:0"></span>{lbl}</div>',
                    unsafe_allow_html=True,
                )

# ═════════════════════════════════════════════════════════════════════════════
# STEP 2 — CONTEXT
# ═════════════════════════════════════════════════════════════════════════════
elif cur == 2:
    if not st.session_state.project_id:
        notice("Complete Step 1 first.", "error"); st.stop()
    if not st.session_state.confirmed_sections:
        notice("Complete Step 2 (Sections) first.", "warn")
        if st.button("← Sections"): go(1); st.rerun()
        st.stop()

    left, right = st.columns([6, 5], gap="large")

    with left:
        st.markdown(
            '<div class="ph"><div class="ph-title">Context Building</div>'
            '<div class="ph-sub">Source files are chunked, embedded with '
            '<code>all-MiniLM-L6-v2</code> entirely on your CPU, '
            'and stored in ChromaDB. Nothing leaves your machine.</div></div>',
            unsafe_allow_html=True,
        )

        a = st.session_state.analysis or {}
        loc = a.get("total_loc", 0)
        strat = "RAPTOR — Hierarchical Tree" if loc > 50000 else "Flat Chunking"
        note  = ("Codebase exceeds 50K LOC — RAPTOR builds a multi-level summary tree."
                 if loc > 50000 else "Under 50K LOC — flat chunking is sufficient.")
        st.markdown(
            f'<div class="card-blue">'
            f'<div style="font-size:0.6rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#6b8af0;margin-bottom:0.3rem">Auto-selected strategy</div>'
            f'<div style="font-size:1rem;font-weight:700;color:#1d4ed8;margin-bottom:0.2rem">{strat}</div>'
            f'<div style="font-size:0.73rem;color:#6b8af0">{note}</div></div>',
            unsafe_allow_html=True,
        )

        if st.session_state.context_result:
            r = st.session_state.context_result
            notice("Vector database already built. Rebuild only if the codebase changed.", "ok")
            m = st.columns(3)
            with m[0]: mc("Strategy",      r["strategy"].upper())
            with m[1]: mc("Chunks Stored", f"{r['total_chunks']:,}")
            with m[2]: mc("DB Size",       f"{r['vector_db_size_mb']} MB")
            st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
            if st.button("Continue to Generation →", use_container_width=True): go(3); st.rerun()
        else:
            notice("Runs entirely on your machine. Expect 1–5 min depending on CPU.", "info")
            if st.button("Build Context Database", use_container_width=True, key="build_ctx"):
                bar = st.progress(0, text="Initialising…")
                for p, msg in [(10,"Filtering…"),(30,"Chunking…"),(60,"Embedding (longest step)…"),(88,"Storing…")]:
                    time.sleep(0.4); bar.progress(p, text=msg)
                data, err = api_call("post", "/context/build", json={"project_id": st.session_state.project_id})
                bar.progress(100, text="Complete.")
                if err:
                    notice(f"Build failed: {err}", "error")
                else:
                    st.session_state.context_result = data
                    st.rerun()

    with right:
        slabel("Sections queued")
        for s in st.session_state.confirmed_sections:
            st.markdown(
                f'<div style="font-size:0.8rem;padding:0.4rem 0;border-bottom:1px solid #f0f0ee;color:#374151">{s}</div>',
                unsafe_allow_html=True,
            )

# ═════════════════════════════════════════════════════════════════════════════
# STEP 3 — GENERATE
# ═════════════════════════════════════════════════════════════════════════════
elif cur == 3:
    if not st.session_state.project_id:
        notice("Complete Step 1 first.", "error"); st.stop()
    if not st.session_state.confirmed_sections:
        notice("Complete Step 2 first.", "warn")
        if st.button("← Sections"): go(1); st.rerun(); st.stop()
    if not st.session_state.context_result:
        notice("Complete Step 3 (Context) first.", "warn")
        if st.button("← Context"): go(2); st.rerun(); st.stop()

    pid      = st.session_state.project_id
    sections = st.session_state.confirmed_sections
    total    = len(sections)

    st.markdown(
        '<div class="ph"><div class="ph-title">Section Generation</div>'
        '<div class="ph-sub">Each section is written via RAG using the most relevant code chunks. '
        'Sections scoring below 0.7 are automatically regenerated once.</div></div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.get("generation_started"):
        notice(f"Ready to generate <b>{total} sections</b> via Groq. Expect 10–30 s per section.", "info")
        if st.button("Start Generation", use_container_width=True, key="start_gen"):
            data, err = api_call("post", f"/generate/start/{pid}")
            if err:
                notice(f"Failed: {err}", "error")
            else:
                st.session_state.generation_started = True; st.rerun()
        st.stop()

    status_data, err = api_call("get", f"/generate/status/{pid}")
    if err:
        notice(f"Status error: {err}", "error"); st.stop()

    finished    = status_data["finished"]
    completed   = status_data["completed"]
    in_progress = status_data.get("in_progress")
    sec_states  = status_data["sections"]

    st.progress(completed / max(total, 1), text=f"{'Done' if finished else 'Generating'}… {completed}/{total}")
    st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)

    slabel("Section progress")
    for sec_name in sections:
        s       = sec_states.get(sec_name, {})
        state   = s.get("status", "pending")
        score   = s.get("quality_score")
        is_ip   = (sec_name == in_progress or state == "in_progress")

        if is_ip:
            bg, border, badge = "#eff6ff","#bfdbfe", '<span class="badge b-blue">Generating…</span>'
        elif state == "success":
            bg, border, badge = "#f0fdf4","#bbf7d0", f'<span class="badge b-green">{score}</span>'
        elif state == "low_quality":
            bg, border, badge = "#fffbeb","#fde68a", f'<span class="badge b-amber">{score}</span>'
        elif state == "failed":
            bg, border, badge = "#fff5f5","#fecaca", '<span class="badge b-red">Failed</span>'
        else:
            bg, border, badge = "#fafafa","#e5e7eb", '<span class="badge b-gray">Pending</span>'

        st.markdown(
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'padding:0.65rem 1rem;border-radius:8px;border:1px solid {border};background:{bg};margin-bottom:0.28rem">'
            f'<span style="font-size:0.81rem;font-weight:500;color:#374151">{sec_name}</span>{badge}</div>',
            unsafe_allow_html=True,
        )

    if not finished:
        time.sleep(3); st.rerun()
    else:
        st.session_state.generation_finished = True
        if not st.session_state.get("generation_results"):
            r, e = api_call("get", f"/generate/results/{pid}")
            if not e and r:
                st.session_state.generation_results = r.get("sections", [])
        success_n = sum(1 for s in sec_states.values() if s["status"] == "success")
        notice(f"Generation complete — {success_n}/{total} sections succeeded.", "ok")
        if st.button("Continue to Review →", use_container_width=True): go(4); st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# STEP 4 — REVIEW  (includes reorder + inline edit + approve/reject)
# ═════════════════════════════════════════════════════════════════════════════
elif cur == 4:
    if not st.session_state.project_id:
        notice("Complete Step 1 first.", "error"); st.stop()
    if not st.session_state.generation_finished:
        notice("Complete Step 4 (Generate) first.", "warn")
        if st.button("← Generate"): go(3); st.rerun(); st.stop()

    pid      = st.session_state.project_id
    gen_secs = get_gen_sections()

    if not gen_secs:
        # Try fetching from API
        r, e = api_call("get", f"/generate/results/{pid}")
        if not e and r:
            st.session_state.generation_results = r.get("sections", [])
            gen_secs = get_gen_sections()
    if not gen_secs:
        notice("No generated sections found. Go back and re-run generation.", "error")
        if st.button("← Generate"): go(3); st.rerun()
        st.stop()

    # Seed review state on first load
    valid_init = [{"name": s["name"], "content": s["content"],
                   "order": s["order"], "quality_score": s["quality_score"]}
                  for s in gen_secs if s["name"]]
    if valid_init:
        api_call("post", f"/review/{pid}/init", json={"sections": valid_init})

    # Ensure section_order is populated
    if not st.session_state.section_order:
        st.session_state.section_order = [s["name"] for s in sorted(gen_secs, key=lambda x: x["order"])]

    st.markdown(
        '<div class="ph"><div class="ph-title">Review & Arrange</div>'
        '<div class="ph-sub">Edit content, approve or reject sections, and drag them into '
        'the order you want in the final document before assembly.</div></div>',
        unsafe_allow_html=True,
    )

    # ── Summary metrics ──────────────────────────────────────────────────────
    decisions = st.session_state.review_decisions
    approved  = sum(1 for v in decisions.values() if v.get("action") == "approve")
    rejected  = sum(1 for v in decisions.values() if v.get("action") == "reject")
    pending   = len(gen_secs) - approved - rejected
    avg_q = (sum(s["quality_score"] for s in gen_secs if s.get("quality_score")) / max(len(gen_secs), 1))

    m = st.columns(4)
    with m[0]: mc("Total",    str(len(gen_secs)))
    with m[1]: mc("Approved", str(approved), "sections")
    with m[2]: mc("Pending",  str(pending),  "sections")
    with m[3]: mc("Avg Qual", f"{avg_q:.0%}")

    st.markdown('<div style="height:0.75rem"></div>', unsafe_allow_html=True)

    # ── Two tabs: Review | Reorder ────────────────────────────────────────────
    tab_rev, tab_ord = st.tabs(["Review Sections", "Arrange Order"])

    with tab_rev:
        # Build a map for quick lookup
        sec_map = {s["name"]: s for s in gen_secs}

        for sec_name in st.session_state.section_order:
            sec = sec_map.get(sec_name)
            if not sec: continue

            score     = sec.get("quality_score", 0.0)
            dec       = decisions.get(sec_name, {})
            status    = dec.get("action", "pending")
            score_cls = "b-green" if score >= 0.7 else "b-amber" if score >= 0.5 else "b-red"
            sta_cls   = "b-green" if status == "approve" else "b-red" if status == "reject" else "b-gray"
            sta_lbl   = status.upper() if status != "pending" else "PENDING"

            with st.expander(
                f"{sec_name}  —  {len(sec['content'].split()):,} words",
                expanded=(status == "pending"),
            ):
                hd = st.columns([3, 1])
                with hd[0]:
                    st.markdown(
                        f'<span class="badge {sta_cls}">{sta_lbl}</span>'
                        f'<span class="badge {score_cls}" style="margin-left:0.4rem">Quality {int(score*100)}</span>',
                        unsafe_allow_html=True,
                    )
                with hd[1]:
                    if st.button("Regenerate", key=f"regen_{sec_name}", use_container_width=True):
                        with st.spinner("Regenerating…"):
                            r, e = api_call("post", f"/review/{pid}/regenerate",
                                            json={"section_name": sec_name})
                        if e:
                            notice(f"Regeneration failed: {e}", "error")
                        else:
                            # Update local cache with new content
                            new_content = r.get("result", {}).get("content", sec["content"])
                            for gs in st.session_state.generation_results:
                                if (gs.get("name") or gs.get("section_name")) == sec_name:
                                    gs["content"] = new_content
                                    gs["quality_score"] = r.get("result", {}).get("quality_score", score)
                            notice(f"'{sec_name}' regenerated.", "ok")
                            st.rerun()

                current_content = dec.get("edited_content") or sec["content"]
                edited = st.text_area("Content (edit freely)", value=current_content, height=280,
                                      key=f"edit_{sec_name}")
                note_val = st.text_input("Reviewer note (optional)", key=f"note_{sec_name}")

                ca, cr = st.columns(2)
                with ca:
                    if st.button("✓  Approve", key=f"app_{sec_name}", use_container_width=True):
                        st.session_state.review_decisions[sec_name] = {
                            "action": "approve",
                            "edited_content": edited if edited != sec["content"] else None,
                            "note": note_val or None,
                        }
                        api_call("post", f"/review/{pid}/decide", json={
                            "section_name": sec_name, "action": "approve",
                            "edited_content": edited if edited != sec["content"] else None,
                            "note": note_val or None,
                        })
                        st.rerun()
                with cr:
                    if st.button("✕  Reject", key=f"rej_{sec_name}", use_container_width=True):
                        st.session_state.review_decisions[sec_name] = {
                            "action": "reject", "edited_content": None, "note": note_val or None,
                        }
                        api_call("post", f"/review/{pid}/decide", json={
                            "section_name": sec_name, "action": "reject",
                            "edited_content": None, "note": note_val or None,
                        })
                        st.rerun()

    with tab_ord:
        st.markdown(
            '<div style="font-size:0.78rem;color:#6b7280;margin-bottom:1rem">'
            'Use the ↑ ↓ buttons to move sections. This order will be used in the assembled document.</div>',
            unsafe_allow_html=True,
        )
        order = st.session_state.section_order
        for i, sec_name in enumerate(order):
            ca, cb, cc = st.columns([6, 1, 1])
            with ca:
                dec = decisions.get(sec_name, {})
                sta = dec.get("action", "pending")
                dot_color = "#15803d" if sta == "approve" else "#dc2626" if sta == "reject" else "#d1d5db"
                st.markdown(
                    f'<div class="reorder-row">'
                    f'<span class="reorder-num">{i+1:02d}</span>'
                    f'<span style="width:8px;height:8px;border-radius:50%;background:{dot_color};flex-shrink:0"></span>'
                    f'{sec_name}</div>',
                    unsafe_allow_html=True,
                )
            with cb:
                if i > 0 and st.button("↑", key=f"up_{i}", use_container_width=True):
                    order[i], order[i-1] = order[i-1], order[i]
                    st.session_state.section_order = order
                    st.rerun()
            with cc:
                if i < len(order) - 1 and st.button("↓", key=f"dn_{i}", use_container_width=True):
                    order[i], order[i+1] = order[i+1], order[i]
                    st.session_state.section_order = order
                    st.rerun()

    hr()
    if pending > 0:
        notice(f"<b>{pending}</b> section(s) still pending review. You can still proceed.", "warn")

    if st.button("Continue to Assembly →", use_container_width=True, key="go_assemble"):
        go(5); st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# STEP 5 — ASSEMBLE
# ═════════════════════════════════════════════════════════════════════════════
elif cur == 5:
    if not st.session_state.project_id:
        notice("Complete Step 1 first.", "error"); st.stop()
    if not st.session_state.generation_finished:
        notice("Complete generation first.", "warn")
        if st.button("← Generate"): go(3); st.rerun(); st.stop()

    pid      = st.session_state.project_id
    gen_secs = get_gen_sections()
    order    = st.session_state.section_order or [s["name"] for s in gen_secs]
    decisions = st.session_state.review_decisions

    # Build final ordered section list — use edited content when available
    ordered_sections = []
    sec_map = {s["name"]: s for s in gen_secs}
    for i, name in enumerate(order):
        sec = sec_map.get(name)
        if not sec: continue
        dec = decisions.get(name, {})
        if dec.get("action") == "reject":
            continue  # skip rejected
        ordered_sections.append({
            "name":          name,
            "content":       dec.get("edited_content") or sec["content"],
            "order":         i,
            "quality_score": sec.get("quality_score", 0.0),
        })

    left, right = st.columns([6, 5], gap="large")

    with left:
        st.markdown(
            '<div class="ph"><div class="ph-title">Document Assembly & Delivery</div>'
            '<div class="ph-sub">Assemble sections into a .docx with title page, '
            'table of contents, and headers. Then download or send by email.</div></div>',
            unsafe_allow_html=True,
        )

        if st.session_state.assembly_result:
            r = st.session_state.assembly_result
            notice("Document assembled successfully.", "ok")
            m = st.columns(3)
            with m[0]: mc("Est. Word Count", f"{r['word_count']:,}")
            with m[1]: mc("Est. Pages", str(r["page_estimate"]))
            with m[2]: mc("Sections",   str(r["section_count"]))
            hr()
            slabel("Download")
            # .docx download
            docx_path = r.get("file_path", "")
            try:
                with open(docx_path, "rb") as f:
                    fname = st.session_state.metadata.get("project_name","document").replace(" ","_")
                    st.download_button(
                        "Download .docx",
                        data=f.read(),
                        file_name=f"{fname}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                    )
            except FileNotFoundError:
                notice(f"File not found at {docx_path}. Try re-assembling.", "error")

            # PDF download
            pdf_path = docx_path.replace(".docx", ".pdf")
            try:
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        "Download .pdf",
                        data=f.read(),
                        file_name=f"{fname}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
            except FileNotFoundError:
                pdf_data, pdf_err = api_call("post", f"/assemble/{pid}/export-pdf")
                if not pdf_err:
                    try:
                        with open(pdf_path, "rb") as f:
                            fname = st.session_state.metadata.get("project_name","document").replace(" ","_")
                            st.download_button(
                                "Download .pdf",
                                data=f.read(),
                                file_name=f"{fname}.pdf",
                                mime="application/pdf",
                                use_container_width=True,
                            )
                    except Exception:
                        pass

            hr()
            slabel("Send by email")
            recipients_raw = st.text_input("Recipients", placeholder="alice@acme.com, bob@acme.com")
            subj = st.text_input("Subject", placeholder=f"Technical Documentation — {st.session_state.metadata.get('project_name','')}")
            msg  = st.text_area("Message (optional)", height=80)
            if st.button("Send Document", use_container_width=True, key="send_email"):
                recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]
                if not recipients:
                    st.error("Enter at least one recipient.")
                else:
                    with st.spinner("Sending…"):
                        result, err = api_call("post", f"/publish/{pid}/email", json={
                            "project_name": st.session_state.metadata.get("project_name",""),
                            "docx_path": docx_path,
                            "recipients": recipients,
                            "subject": subj or None,
                            "message": msg or None,
                        })
                    if err:
                        notice(f"Delivery failed: {err}", "error")
                    else:
                        notice(f"Sent to {', '.join(recipients)}", "ok")

            hr()
            if st.button("Re-assemble with changes", key="reassemble"):
                st.session_state.assembly_result = None; st.rerun()

        else:
            if not ordered_sections:
                notice("All sections were rejected or no sections available. Go back to Review.", "error")
                if st.button("← Review"): go(4); st.rerun()
                st.stop()

            slabel(f"{len(ordered_sections)} sections ready to assemble")
            for i, sec in enumerate(ordered_sections):
                wc = len(sec["content"].split())
                q  = sec.get("quality_score", 0)
                qc = "b-green" if q >= 0.7 else "b-amber" if q >= 0.5 else "b-red"
                dec_name = decisions.get(sec["name"], {}).get("action", "pending")
                dc = "b-green" if dec_name == "approve" else "b-gray"
                st.markdown(
                    f'<div class="card" style="display:flex;justify-content:space-between;'
                    f'align-items:center;padding:0.65rem 1rem">'
                    f'<div style="display:flex;align-items:center;gap:0.6rem">'
                    f'<span style="font-size:0.62rem;color:#9ca3af;font-weight:700;width:20px">{i+1:02d}</span>'
                    f'<span style="font-size:0.82rem;font-weight:600;color:#374151">{sec["name"]}</span>'
                    f'</div><div style="display:flex;gap:0.4rem;align-items:center">'
                    f'<span style="font-size:0.67rem;color:#9ca3af">{wc:,} w</span>'
                    f'<span class="badge {qc}">{int(q*100)}</span>'
                    f'<span class="badge {dc}">{dec_name.upper()}</span>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

            st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
            if st.button("Assemble Document", use_container_width=True, key="btn_assemble"):
                bar = st.progress(0, text="Preparing…")
                for p, msg in [(20,"Rendering title page…"),(45,"Building table of contents…"),
                               (65,"Formatting sections…"),(85,"Adding headers & footers…"),(95,"Saving…")]:
                    time.sleep(0.35); bar.progress(p, text=msg)
                payload = {
                    "project_id": pid,
                    "metadata":   st.session_state.metadata,
                    "sections":   ordered_sections,
                }
                data, err = api_call("post", f"/api/assemble/{pid}", json=payload)
                bar.progress(100, text="Done.")
                if err:
                    notice(f"Assembly failed: {err}", "error")
                else:
                    st.session_state.assembly_result = data
                    st.rerun()

    with right:
        st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)
        slabel("Section order for assembly")
        for i, name in enumerate(order):
            if name not in [s["name"] for s in ordered_sections]:
                continue
            dec = decisions.get(name, {}).get("action", "pending")
            dot = "#15803d" if dec == "approve" else "#9ca3af"
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:0.6rem;padding:0.4rem 0;'
                f'border-bottom:1px solid #f0f0ee">'
                f'<span style="font-size:0.62rem;color:#9ca3af;width:18px">{i+1}</span>'
                f'<span style="width:7px;height:7px;border-radius:50%;background:{dot};flex-shrink:0"></span>'
                f'<span style="font-size:0.78rem;color:#374151">{name}</span></div>',
                unsafe_allow_html=True,
            )
        if decisions:
            hr()
            slabel("Review summary")
            approved_n = sum(1 for v in decisions.values() if v.get("action") == "approve")
            rejected_n = sum(1 for v in decisions.values() if v.get("action") == "reject")
            edited_n   = sum(1 for v in decisions.values() if v.get("edited_content"))
            st.markdown(
                f'<div style="font-size:0.78rem;color:#374151">'
                f'<div style="margin-bottom:0.3rem">✓ Approved: <b>{approved_n}</b></div>'
                f'<div style="margin-bottom:0.3rem">✕ Rejected: <b>{rejected_n}</b></div>'
                f'<div>✎ Edited: <b>{edited_n}</b></div></div>',
                unsafe_allow_html=True,
            )