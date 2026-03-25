import streamlit as st
import requests
import json
import time

st.set_page_config(
    page_title="DocAgent",
    layout="wide",
    initial_sidebar_state="collapsed",
)

API_BASE = "http://localhost:8000"

def lucide(name, size=16, color="%23666"):
    return (
        f'<img src="https://api.iconify.design/lucide/{name}.svg?color={color}" '
        f'width="{size}" height="{size}" '
        f'style="display:inline-block;vertical-align:middle;flex-shrink:0;">'
    )

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background-color: #f8f9fb !important;
    color: #1a1d23 !important;
}

#MainMenu, footer, header, [data-testid="stSidebar"] { display: none !important; }

.block-container {
    padding: 0 2.5rem 6rem 2.5rem !important;
    max-width: 1180px !important;
    margin: 0 auto !important;
}

.topbar {
    display: flex; align-items: center;
    justify-content: space-between;
    padding: 1rem 0 1.1rem 0;
    margin-bottom: 0.25rem;
    border-bottom: 1px solid #e8eaed;
    background: #f8f9fb;
}
.brand {
    display: flex; align-items: center; gap: 0.5rem;
    font-size: 0.9rem; font-weight: 700;
    color: #111318; letter-spacing: -0.02em;
}
.brand-accent { color: #4f6ef7; }
.breadcrumb {
    display: flex; align-items: center; gap: 0.4rem;
    font-size: 0.72rem; color: #9aa0ad;
    padding-left: 0.9rem; margin-left: 0.9rem;
    border-left: 1px solid #e8eaed;
}

.badge {
    display: inline-flex; align-items: center; gap: 0.3rem;
    padding: 0.22rem 0.65rem; border-radius: 4px;
    font-size: 0.67rem; font-weight: 600;
    letter-spacing: 0.04em; text-transform: uppercase;
}
.badge-green  { background: #edfaf3; color: #1a7a46; border: 1px solid #c3ecd6; }
.badge-red    { background: #fff0f0; color: #c0392b; border: 1px solid #f5c6c6; }
.badge-blue   { background: #eff3ff; color: #4f6ef7; border: 1px solid #c7d4fd; }
.badge-amber  { background: #fffbeb; color: #b45309; border: 1px solid #fde68a; }
.badge-gray   { background: #f1f3f5; color: #6b7280; border: 1px solid #d1d5db; }

.page-head { margin-bottom: 1.75rem; padding-top: 0.25rem; }
.page-head-title {
    font-size: 1.25rem; font-weight: 700;
    color: #111318; letter-spacing: -0.025em;
    display: flex; align-items: center; gap: 0.55rem;
    margin-bottom: 0.35rem;
}
.page-head-sub { font-size: 0.8rem; color: #6b7280; line-height: 1.7; max-width: 640px; }

.slabel {
    font-size: 0.6rem; font-weight: 700;
    letter-spacing: 0.14em; text-transform: uppercase;
    color: #9aa0ad; margin-bottom: 0.65rem;
    display: flex; align-items: center; gap: 0.5rem;
}
.slabel::after { content: ""; flex: 1; height: 1px; background: #e8eaed; }

.card {
    background: #ffffff; border: 1px solid #e8eaed;
    border-radius: 10px; padding: 1.2rem 1.35rem; margin-bottom: 0.75rem;
}
.card-blue {
    background: #f5f7ff; border: 1px solid #dce4fd;
    border-radius: 10px; padding: 1.2rem 1.35rem; margin-bottom: 0.75rem;
}
.card-green {
    background: #f3fbf7; border: 1px solid #c3ecd6;
    border-radius: 10px; padding: 1.2rem 1.35rem; margin-bottom: 0.75rem;
}

.mcard {
    background: #ffffff; border: 1px solid #e8eaed;
    border-radius: 10px; padding: 1.1rem 1.2rem;
}
.mcard-icon { margin-bottom: 0.6rem; }
.mcard-label {
    font-size: 0.6rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.1em;
    color: #9aa0ad; margin-bottom: 0.3rem;
}
.mcard-val {
    font-size: 1.6rem; font-weight: 700;
    color: #111318; letter-spacing: -0.04em; line-height: 1;
}
.mcard-sub  { font-size: 0.68rem; color: #9aa0ad; margin-top: 0.18rem; }
.mcard-note {
    font-size: 0.68rem; color: #6b7280; line-height: 1.55;
    margin-top: 0.55rem; padding-top: 0.5rem;
    border-top: 1px solid #f0f0f0;
}

.tag {
    display: inline-block;
    background: #f1f3f5; border: 1px solid #e4e6ea; color: #374151;
    border-radius: 4px; padding: 0.14rem 0.5rem;
    font-size: 0.68rem; font-family: 'SF Mono', 'Fira Code', monospace;
    margin: 0.1rem;
}

.flag {
    display: inline-flex; align-items: center; gap: 0.3rem;
    padding: 0.2rem 0.6rem; border-radius: 4px;
    font-size: 0.68rem; font-weight: 600; margin: 0.1rem;
}
.flag-on  { background: #edfaf3; color: #1a7a46; border: 1px solid #c3ecd6; }
.flag-off { background: #f8f9fb; color: #c4c9d4; border: 1px solid #e8eaed; }

.notice {
    display: flex; gap: 0.75rem; align-items: flex-start;
    padding: 0.85rem 1rem; border-radius: 8px;
    font-size: 0.77rem; line-height: 1.65; margin-bottom: 1rem;
}
.notice-info  { background: #f0f4ff; border: 1px solid #c7d4fd; color: #3451c7; }
.notice-ok    { background: #f0faf5; border: 1px solid #b9e8ce; color: #1a7a46; }
.notice-warn  { background: #fffceb; border: 1px solid #fde68a; color: #92400e; }
.notice-error { background: #fff5f5; border: 1px solid #fecaca; color: #b91c1c; }

.scard { border-radius: 8px; padding: 0.85rem 1rem; margin-bottom: 0.45rem; border: 1px solid; }
.scard-on  { background: #f0faf5; border-color: #b9e8ce; }
.scard-off { background: #ffffff; border-color: #e8eaed; }
.scard-name { font-size: 0.82rem; font-weight: 600; margin-bottom: 0.12rem; }
.scard-name-on  { color: #1a7a46; }
.scard-name-off { color: #9aa0ad; }
.scard-reason { font-size: 0.69rem; line-height: 1.5; }
.scard-reason-on  { color: #3d9e68; }
.scard-reason-off { color: #c4c9d4; }

.cbadge {
    display: inline-flex; align-items: center;
    background: #f0f4ff; border: 1px solid #c7d4fd;
    color: #4f6ef7; border-radius: 5px;
    padding: 0.22rem 0.65rem; font-size: 0.72rem;
    font-weight: 500; margin: 0.15rem;
}

.pline {
    display: flex; align-items: center; gap: 0.9rem;
    padding: 0.75rem 1rem; border-radius: 8px;
    border: 1px solid; margin-bottom: 0.3rem;
}
.pline-done   { background: #f0faf5; border-color: #b9e8ce; }
.pline-locked { background: #fafafa; border-color: #f0f0f0; }
.pline-dot {
    width: 24px; height: 24px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.pline-dot-done   { background: #d1f5e3; border: 1px solid #86efac; }
.pline-dot-locked { background: #f1f3f5; border: 1px solid #e4e6ea; }
.pline-phase { font-size: 0.6rem; font-weight: 700; letter-spacing: 0.08em; width: 56px; flex-shrink: 0; color: #9aa0ad; }
.pline-name { font-size: 0.82rem; font-weight: 500; }
.pline-name-done   { color: #1a7a46; }
.pline-name-locked { color: #c4c9d4; }

.hw-step { display: flex; gap: 0.85rem; padding: 0.8rem 0; border-bottom: 1px solid #f0f0f0; }
.hw-step:last-child { border-bottom: none; }
.hw-num {
    width: 22px; height: 22px; border-radius: 5px;
    background: #eff3ff; border: 1px solid #c7d4fd; color: #4f6ef7;
    font-size: 0.65rem; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; margin-top: 1px;
}
.hw-title { font-size: 0.79rem; font-weight: 600; color: #374151; margin-bottom: 0.18rem; }
.hw-desc  { font-size: 0.71rem; color: #9aa0ad; line-height: 1.6; }

.stat-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.42rem 0; border-bottom: 1px solid #f5f5f5;
}
.stat-label { font-size: 0.72rem; color: #9aa0ad; display: flex; align-items: center; gap: 0.4rem; }
.stat-val   { font-size: 0.75rem; font-weight: 600; color: #374151; }

.hr { border: none; border-top: 1px solid #f0f0f0; margin: 1.4rem 0; }

.stTextInput > label, .stTextArea > label, .stFileUploader > label {
    font-size: 0.62rem !important; font-weight: 700 !important;
    letter-spacing: 0.1em !important; text-transform: uppercase !important;
    color: #9aa0ad !important;
}
.stTextInput input {
    background: #ffffff !important; border: 1px solid #e4e6ea !important;
    border-radius: 7px !important; color: #1a1d23 !important;
    font-size: 0.83rem !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
}
.stTextInput input:focus {
    border-color: #4f6ef7 !important;
    box-shadow: 0 0 0 3px rgba(79,110,247,0.1) !important;
}
.stTextInput input::placeholder { color: #c4c9d4 !important; }
.stTextArea textarea {
    background: #ffffff !important; border: 1px solid #e4e6ea !important;
    border-radius: 7px !important; color: #1a1d23 !important;
    font-size: 0.83rem !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
}
.stTextArea textarea:focus {
    border-color: #4f6ef7 !important;
    box-shadow: 0 0 0 3px rgba(79,110,247,0.1) !important;
}
.stTextArea textarea::placeholder { color: #c4c9d4 !important; }

.stButton > button {
    background: #4f6ef7 !important; border: 1px solid #4f6ef7 !important;
    color: #ffffff !important; border-radius: 7px !important;
    font-size: 0.78rem !important; font-weight: 600 !important;
    padding: 0.48rem 1.3rem !important; transition: all 0.15s ease !important;
    box-shadow: 0 1px 3px rgba(79,110,247,0.25) !important;
}
.stButton > button:hover {
    background: #3d5ce8 !important; border-color: #3d5ce8 !important;
    box-shadow: 0 3px 10px rgba(79,110,247,0.3) !important;
}

[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid #e8eaed !important; gap: 0 !important;
}
[data-testid="stTabs"] button[role="tab"] {
    font-size: 0.76rem !important; font-weight: 500 !important;
    color: #9aa0ad !important; background: transparent !important;
    border: none !important; border-radius: 0 !important;
    padding: 0.55rem 1.1rem !important;
}
[data-testid="stTabs"] button[role="tab"]:hover { color: #374151 !important; }
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: #4f6ef7 !important;
    border-bottom: 2px solid #4f6ef7 !important;
    font-weight: 600 !important;
}

.stProgress > div > div { background: #4f6ef7 !important; border-radius: 3px !important; }
.stCheckbox label span { font-size: 0.8rem !important; color: #374151 !important; }
[data-testid="stFileUploadDropzone"] {
    background: #ffffff !important; border: 1.5px dashed #d1d5db !important;
    border-radius: 8px !important;
}
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #f8f9fb; }
::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #b0b7c3; }
</style>
""", unsafe_allow_html=True)

# ── Session state
DEFAULTS = {
    "page": 0, "project_id": None,
    "analysis": None, "metadata": {},
    "suggestions": [], "confirmed_sections": [],
    "context_result": None, "last_action": None,
    "assembly_result": None,
    "generation_results": [],        # ← ADD THIS
    "generation_started": False,     # ← ADD THIS
    "generation_finished": False,    # ← ADD THIS
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Helpers
def api_call(method, endpoint, **kwargs):
    try:
        r = getattr(requests, method)(f"{API_BASE}{endpoint}", timeout=180, **kwargs)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "connection_error"
    except requests.exceptions.HTTPError as e:
        try:    detail = e.response.json().get("detail", str(e))
        except: detail = str(e)
        return None, detail
    except Exception as e:
        return None, str(e)

def api_online():
    d, _ = api_call("get", "/health")
    return d is not None

def go(i):
    st.session_state.page = i

def mcard(label, val, sub="", note="", icon_name=""):
    ico  = lucide(icon_name, 15, "%239aa0ad") if icon_name else ""
    irow = f'<div class="mcard-icon">{ico}</div>' if icon_name else ""
    nrow = f'<div class="mcard-note">{note}</div>' if note else ""
    srow = f'<div class="mcard-sub">{sub}</div>' if sub else ""
    st.markdown(
        f'<div class="mcard">{irow}<div class="mcard-label">{label}</div>'
        f'<div class="mcard-val">{val}</div>{srow}{nrow}</div>',
        unsafe_allow_html=True
    )

def tagrow(items):
    if not items: items = ["—"]
    st.markdown("".join(f'<span class="tag">{i}</span>' for i in items), unsafe_allow_html=True)

def notice(msg, kind="info", icon_name="info"):
    ico = lucide(icon_name, 15, "currentColor")
    st.markdown(
        f'<div class="notice notice-{kind}">{ico}<span>{msg}</span></div>',
        unsafe_allow_html=True
    )

def slabel(text):
    st.markdown(f'<div class="slabel">{text}</div>', unsafe_allow_html=True)

def hr():
    st.markdown('<hr class="hr">', unsafe_allow_html=True)


# ── API check
online = api_online()

# ── TOPBAR
brand_ico    = lucide("file-text", 17, "%234f6ef7")
folder_ico   = lucide("folder", 11, "%239aa0ad")
status_badge = '<span class="badge badge-green">&#9679; Live</span>' if online else '<span class="badge badge-red">&#9679; Offline</span>'

crumb = ""
if st.session_state.project_id:
    pname = st.session_state.metadata.get("project_name", "Unnamed")
    pid   = st.session_state.project_id[:10] + "..."
    crumb = (
        f'<div class="breadcrumb">{folder_ico}&nbsp;{pname}&nbsp;&nbsp;'
        f'<span style="color:#c4c9d4;font-family:monospace;font-size:0.65rem;">{pid}</span></div>'
    )

st.markdown(
    f'<div class="topbar">'
    f'<div style="display:flex;align-items:center;">'
    f'<div class="brand">{brand_ico}&nbsp;Doc<span class="brand-accent">Agent</span></div>'
    f'{crumb}</div>'
    f'<div>{status_badge}</div></div>',
    unsafe_allow_html=True
)

if not online:
    notice(
        'API server not responding. Start it with '
        '<code style="background:#fff0f0;color:#c0392b;padding:0.1rem 0.3rem;border-radius:3px;">python run.py</code> then refresh.',
        "error", "alert-circle"
    )


# ── STEPPER
done = [
    bool(st.session_state.analysis),
    bool(st.session_state.confirmed_sections),
    bool(st.session_state.context_result),
    bool(st.session_state.get("generation_finished")),
    bool(st.session_state.get("assembly_result")),
    False,  # review
]
STEPS = [
    ("01", "Ingest"),
    ("02", "Sections"),
    ("03", "Context"),
    ("04", "Generate"),
    ("05", "Assemble"),
    ("06", "Review"),
]

cur   = st.session_state.page


st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
step_cols = st.columns(len(STEPS))
for i, (col, (num, lbl)) in enumerate(zip(step_cols, STEPS)):
    state = "done" if (done[i] and i != cur) else "active" if i == cur else "idle"
    with col:
        if st.button(f"{num} · {lbl}", key=f"nav_{i}", use_container_width=True):
            go(i); st.rerun()
        bar_color = "#22c55e" if state == "done" else "#4f6ef7" if state == "active" else "#e8eaed"
        st.markdown(
            f'<div style="height:2px;background:{bar_color};margin-top:-13px;"></div>',
            unsafe_allow_html=True
        )

st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# PAGE 0 — INGEST
# ══════════════════════════════════════════════════════
if cur == 0:
    left, right = st.columns([17, 6], gap="large")

    with left:
        ph_ico = lucide("upload-cloud", 20, "%234f6ef7")
        st.markdown(
            f'<div class="page-head">'
            f'<div class="page-head-title">{ph_ico} Ingest Codebase</div>'
            f'<div class="page-head-sub">Provide a GitHub repository or a ZIP archive. '
            f'Noise is stripped automatically — node_modules, binaries, lock files — '
            f'reducing transfer size by up to 90% before analysis begins.</div></div>',
            unsafe_allow_html=True
        )

        gh_tab, zip_tab = st.tabs(["  GitHub Repository  ", "  ZIP Archive  "])

        with gh_tab:
            c1, c2 = st.columns(2, gap="large")
            with c1:
                slabel("Source")
                gh_url   = st.text_input("Repository URL", placeholder="https://github.com/owner/repo")
                gh_token = st.text_input("Access Token", type="password",
                    placeholder="ghp_...  (optional for public repos)",
                    help="Deleted from memory immediately after clone.")
            with c2:
                slabel("Metadata")
                gh_name   = st.text_input("Project Name",  placeholder="My API Service")
                gh_client = st.text_input("Client",        placeholder="Acme Corp")
                gh_team   = st.text_input("Team Members",  placeholder="Alice, Bob")
                gh_desc   = st.text_area("Description",    placeholder="What does this project do?", height=72)
            hr()
            if online and st.button("Clone & Analyze Repository", key="btn_gh"):
                if not gh_url.strip() or not gh_name.strip() or not gh_client.strip():
                    st.error("Repository URL, Project Name and Client are required.")
                else:
                    bar = st.progress(0, text="Connecting...")
                    for p, msg in [(10,"Cloning..."),(35,"Filtering..."),(65,"Analyzing stack..."),(88,"Finalizing...")]:
                        time.sleep(0.3); bar.progress(p, text=msg)
                    payload = {
                        "source_type": "github", "github_url": gh_url.strip(),
                        "github_token": gh_token.strip() or None,
                        "metadata": {
                            "project_name": gh_name.strip(), "client_name": gh_client.strip(),
                            "team_members": [m.strip() for m in gh_team.split(",") if m.strip()],
                            "description": gh_desc.strip(),
                        }
                    }
                    data, err = api_call("post", "/ingest/github", json=payload)
                    bar.progress(100, text="Done.")
                    if err:
                        notice(f"Ingestion failed — {err}", "error", "alert-circle")
                    else:
                        st.session_state.update({
                            "project_id": data["project_id"],
                            "analysis":   data["analysis"],
                            "metadata":   payload["metadata"],
                            "last_action":"ingest",
                        })
                        st.rerun()

        with zip_tab:
            c1, c2 = st.columns(2, gap="large")
            with c1:
                slabel("Archive")
                zfile = st.file_uploader("ZIP File", type=["zip"],
                    help="node_modules and build artifacts stripped automatically.")
            with c2:
                slabel("Metadata")
                z_name   = st.text_input("Project Name  ", placeholder="My Project")
                z_client = st.text_input("Client  ",       placeholder="Acme Corp")
                z_team   = st.text_input("Team Members  ", placeholder="Alice, Bob")
                z_desc   = st.text_area("Description  ",   placeholder="What does this project do?", height=72)
            hr()
            if online and st.button("Extract & Analyze Archive", key="btn_zip"):
                if not zfile or not z_name.strip() or not z_client.strip():
                    st.error("ZIP file, Project Name and Client are required.")
                else:
                    bar = st.progress(0, text="Reading archive...")
                    for p, msg in [(15,"Extracting..."),(45,"Filtering..."),(72,"Analyzing..."),(90,"Finalizing...")]:
                        time.sleep(0.3); bar.progress(p, text=msg)
                    data, err = api_call("post", "/ingest/zip",
                        files={"file": (zfile.name, zfile.getvalue(), "application/zip")},
                        data={
                            "project_name": z_name.strip(),
                            "client_name":  z_client.strip(),
                            "team_members": json.dumps([m.strip() for m in z_team.split(",") if m.strip()]),
                            "description":  z_desc.strip(),
                        })
                    bar.progress(100, text="Done.")
                    if err:
                        notice(f"Extraction failed — {err}", "error", "alert-circle")
                    else:
                        st.session_state.update({
                            "project_id": data["project_id"],
                            "analysis":   data["analysis"],
                            "metadata": {
                                "project_name": z_name, "client_name": z_client,
                                "team_members": [m.strip() for m in z_team.split(",") if m.strip()],
                                "description":  z_desc,
                            },
                            "last_action": "ingest",
                        })
                        st.rerun()

        if st.session_state.analysis:
            a   = st.session_state.analysis
            loc = a.get("total_loc", 0)
            ep  = a.get("api_endpoints_count", 0)
            hr()
            slabel("Analysis Results")
            notice("Codebase ingested and analyzed successfully.", "ok", "check-circle")

            mc = st.columns(4)
            with mc[0]:
                mcard("Lines of Code", f"{loc:,}", "source LOC",
                      "Above 50K uses RAPTOR strategy." if loc > 50000 else "Below 50K uses Flat strategy.", "code-2")
            with mc[1]:
                mcard("API Endpoints", str(ep), "detected routes",
                      "API docs will be suggested." if ep > 0 else "No routes detected.", "network")
            with mc[2]:
                strat = "RAPTOR" if loc > 50000 else "Flat"
                mcard("Context Strategy", strat, "> 50K LOC" if loc > 50000 else "< 50K LOC",
                      "Hierarchical summary tree." if strat == "RAPTOR" else "Direct chunking.", "git-branch")
            with mc[3]:
                mcard("Files Kept", str(a.get("filtered_file_count", 0)), "after filtering",
                      "Binaries and lock files removed.", "filter")

            st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)
            LBL = "font-size:0.6rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#9aa0ad;margin-bottom:0.4rem;"
            tc = st.columns(3)
            for col, key, lbl in zip(tc, ["languages","frameworks","databases"], ["Languages","Frameworks","Databases"]):
                with col:
                    st.markdown(f'<div style="{LBL}">{lbl}</div>', unsafe_allow_html=True)
                    tagrow(a.get(key) or [])

            if a.get("test_frameworks"):
                st.markdown(f'<div style="{LBL};margin-top:0.75rem;">Test Frameworks</div>', unsafe_allow_html=True)
                tagrow(a.get("test_frameworks"))

            st.markdown("<div style='height:0.65rem'></div>", unsafe_allow_html=True)
            fc = st.columns(5)
            FLAGS = [
                ("has_dockerfile","container","Dockerfile"),
                ("has_cicd","git-merge","CI/CD"),
                ("has_kubernetes","server","Kubernetes"),
                ("has_terraform","cloud","Terraform"),
                ("has_ansible","terminal-square","Ansible"),
            ]
            for col, (k, ico_name, lbl) in zip(fc, FLAGS):
                with col:
                    on  = a.get(k, False)
                    ico = lucide(ico_name, 11, "%231a7a46" if on else "%23c4c9d4")
                    cls = "flag-on" if on else "flag-off"
                    st.markdown(f'<div class="flag {cls}">{ico}&nbsp;{lbl}</div>', unsafe_allow_html=True)

            st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)
            if st.button("Continue to Section Selection →", key="go1"):
                go(1); st.rerun()

    with right:
        st.markdown("<div style='height:4.8rem'></div>", unsafe_allow_html=True)
        slabel("How it works")
        how_steps = [
            ("upload-cloud", "Ingest",    "GitHub URL or ZIP. Up to 90% noise stripped before analysis."),
            ("list-checks",  "Sections",  "AI reviews the detected stack and recommends documentation sections."),
            ("database",     "Context",   "Code chunked, embedded locally, stored in ChromaDB."),
            ("file-text",    "Generate",  "Sections generated via RAG using only the most relevant chunks."),
        ]
        for ico_name, title, desc in how_steps:
            step_ico = lucide(ico_name, 11, "%234f6ef7")
            st.markdown(
                f'<div class="hw-step"><div class="hw-num">{step_ico}</div>'
                f'<div><div class="hw-title">{title}</div>'
                f'<div class="hw-desc">{desc}</div></div></div>',
                unsafe_allow_html=True
            )

        if st.session_state.project_id:
            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            slabel("Active Project")
            pn  = st.session_state.metadata.get("project_name", "—")
            cl  = st.session_state.metadata.get("client_name", "—")
            pid = st.session_state.project_id
            st.markdown(
                f'<div class="card-blue">'
                f'<div style="font-size:0.84rem;font-weight:600;color:#3451c7;margin-bottom:0.2rem;">{pn}</div>'
                f'<div style="font-size:0.7rem;color:#6b8af0;margin-bottom:0.5rem;">Client: {cl}</div>'
                f'<div style="font-family:monospace;font-size:0.58rem;color:#b0bcf8;word-break:break-all;">{pid}</div></div>',
                unsafe_allow_html=True
            )
            if st.button("New Project", key="reset", use_container_width=True):
                for k, v in DEFAULTS.items(): st.session_state[k] = v
                st.rerun()


# ══════════════════════════════════════════════════════
# PAGE 1 — SECTIONS
# ══════════════════════════════════════════════════════
elif cur == 1:
    if not st.session_state.project_id:
        notice("No project loaded — complete Step 01 first.", "error", "alert-circle")
        if st.button("Back to Ingest"): go(0); st.rerun()
        st.stop()

    left, right = st.columns([17, 6], gap="large")

    with left:
        ph_ico = lucide("list-checks", 20, "%234f6ef7")
        st.markdown(
            f'<div class="page-head">'
            f'<div class="page-head-title">{ph_ico} Section Selection</div>'
            f'<div class="page-head-sub">The AI reviews your detected stack and pre-selects the most '
            f'relevant documentation sections. Review, adjust, and add custom entries before confirming.</div></div>',
            unsafe_allow_html=True
        )

        if st.button("Generate Section Suggestions", key="load_sugg"):
            with st.spinner("Analysing stack and generating suggestions..."):
                data, err = api_call("get", f"/sections/suggest/{st.session_state.project_id}")
            if err == "connection_error":
                notice("Cannot reach the API server.", "error", "alert-circle")
            elif err:
                st.error(f"Failed: {err}")
            else:
                st.session_state.suggestions = data["suggestions"]
                st.rerun()

        if st.session_state.suggestions:
            suggs  = st.session_state.suggestions
            rec    = [s for s in suggs if s["selected"]]
            opt    = [s for s in suggs if not s["selected"]]
            chosen = []

            if rec:
                st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)
                slabel(f"Detected in your codebase — {len(rec)} sections")
                notice(f"{len(rec)} sections pre-selected based on your stack. Uncheck anything not needed.", "info", "info")
                cols = st.columns(2, gap="medium")
                for i, s in enumerate(rec):
                    with cols[i % 2]:
                        st.markdown(
                            f'<div class="scard scard-on">'
                            f'<div class="scard-name scard-name-on">{s["name"]}</div>'
                            f'<div class="scard-reason scard-reason-on">{s["reason"]}</div></div>',
                            unsafe_allow_html=True
                        )
                        if st.checkbox("Include", value=True, key=f"c_{s['name']}"):
                            chosen.append(s["name"])

            if opt:
                st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
                slabel(f"Not detected — {len(opt)} optional sections")
                st.markdown(
                    '<div style="font-size:0.73rem;color:#9aa0ad;margin-bottom:0.6rem;">'
                    'Not found in your codebase, but can be enabled manually.</div>',
                    unsafe_allow_html=True
                )
                cols2 = st.columns(2, gap="medium")
                for i, s in enumerate(opt):
                    with cols2[i % 2]:
                        st.markdown(
                            f'<div class="scard scard-off">'
                            f'<div class="scard-name scard-name-off">{s["name"]}</div>'
                            f'<div class="scard-reason scard-reason-off">{s["reason"]}</div></div>',
                            unsafe_allow_html=True
                        )
                        if st.checkbox("Include", value=False, key=f"c_{s['name']}"):
                            chosen.append(s["name"])

            hr()
            slabel("Custom Sections")
            st.markdown(
                '<div style="font-size:0.73rem;color:#9aa0ad;margin-bottom:0.55rem;">'
                'Add comma-separated section titles not covered above.</div>',
                unsafe_allow_html=True
            )
            custom_raw = st.text_input(
                "Titles",
                placeholder="GDPR Compliance, Data Migration Strategy, Multi-Tenancy Design",
                label_visibility="collapsed"
            )
            custom  = [c.strip() for c in custom_raw.split(",") if c.strip()] if custom_raw else []
            all_sec = chosen + custom

            if all_sec:
                hr()
                slabel(f"Queued — {len(all_sec)} sections confirmed")
                st.markdown(
                    "".join(f'<span class="cbadge">{s}</span>' for s in all_sec),
                    unsafe_allow_html=True
                )

            st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)
            c1, _ = st.columns([1, 3])
            with c1:
                if st.button("Confirm & Continue →", use_container_width=True, key="confirm"):
                    if not all_sec:
                        st.error("Select at least one section.")
                    else:
                        with st.spinner("Saving..."):
                            data, err = api_call("post", "/sections/confirm", json={
                                "project_id":         st.session_state.project_id,
                                "confirmed_sections": chosen,
                                "custom_sections":    custom,
                            })
                        if err:
                            st.error(f"Failed: {err}")
                        else:
                            st.session_state.confirmed_sections = data["final_sections"]
                            go(2); st.rerun()
        else:
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            notice(
                "Click <strong>Generate Section Suggestions</strong> to get AI-driven recommendations based on your actual stack.",
                "info", "lightbulb"
            )

    with right:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        if st.session_state.analysis:
            a = st.session_state.analysis
            slabel("Stack Summary")
            rows = [
                ("Total LOC",     f"{a.get('total_loc',0):,}", "code-2"),
                ("Languages",     str(len(a.get("languages",  []))), "code"),
                ("Frameworks",    str(len(a.get("frameworks", []))), "layers"),
                ("Databases",     str(len(a.get("databases",  []))), "database"),
                ("API Endpoints", str(a.get("api_endpoints_count", 0)), "network"),
            ]
            for lbl, val, ico_name in rows:
                row_ico = lucide(ico_name, 11, "%239aa0ad")
                st.markdown(
                    f'<div class="stat-row">'
                    f'<div class="stat-label">{row_ico}&nbsp;{lbl}</div>'
                    f'<div class="stat-val">{val}</div></div>',
                    unsafe_allow_html=True
                )


# ══════════════════════════════════════════════════════
# PAGE 2 — CONTEXT BUILDING
# ══════════════════════════════════════════════════════
elif cur == 2:
    if not st.session_state.project_id:
        notice("No project loaded.", "error", "alert-circle")
        if st.button("Back to Ingest"): go(0); st.rerun()
        st.stop()
    if not st.session_state.confirmed_sections:
        notice("No sections confirmed — complete Step 02 first.", "warn", "alert-triangle")
        if st.button("Back to Sections"): go(1); st.rerun()
        st.stop()

    left, right = st.columns([17, 6], gap="large")

    with left:
        ph_ico = lucide("database", 20, "%234f6ef7")
        st.markdown(
            f'<div class="page-head">'
            f'<div class="page-head-title">{ph_ico} Context Building</div>'
            f'<div class="page-head-sub">Source files are split into 500-token chunks, embedded using '
            f'<code style="background:#f1f3f5;color:#374151;padding:0.1rem 0.3rem;border-radius:3px;font-size:0.77rem;">all-MiniLM-L6-v2</code> '
            f'locally on CPU, and stored in a ChromaDB vector database. Nothing leaves your machine.</div></div>',
            unsafe_allow_html=True
        )

        a     = st.session_state.analysis or {}
        loc   = a.get("total_loc", 0)
        strat = "RAPTOR Hierarchical Tree" if loc > 50000 else "Flat Chunking + Embeddings"
        snote = ("Codebase exceeds 50,000 LOC — RAPTOR builds a multi-level summary tree for deep retrieval."
                 if loc > 50000 else
                 "Codebase is under 50,000 LOC — flat chunking is faster and fully sufficient.")
        gb_ico = lucide("git-branch", 13, "%234f6ef7")
        st.markdown(
            f'<div class="card-blue">'
            f'<div style="font-size:0.6rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;'
            f'color:#6b8af0;margin-bottom:0.4rem;display:flex;align-items:center;gap:0.4rem;">{gb_ico}&nbsp;Auto-Selected Strategy</div>'
            f'<div style="font-size:1.1rem;font-weight:700;color:#3451c7;margin-bottom:0.25rem;">{strat}</div>'
            f'<div style="font-size:0.74rem;color:#6b8af0;line-height:1.55;">{snote}</div></div>',
            unsafe_allow_html=True
        )

        slabel("Pipeline Stages")
        sc = st.columns(4, gap="medium")
        stages = [
            ("filter",    "Filter",  "Remove binaries, lockfiles, node_modules"),
            ("scissors",  "Chunk",   "500-token segments, 50-token overlap"),
            ("cpu",       "Embed",   "all-MiniLM-L6-v2 — fully local"),
            ("hard-drive","Store",   "ChromaDB persistent on disk"),
        ]
        for col, (ico_name, title, desc) in zip(sc, stages):
            with col:
                stage_ico = lucide(ico_name, 18, "%234f6ef7")
                st.markdown(
                    f'<div class="card" style="text-align:center;padding:1rem 0.75rem;">{stage_ico}'
                    f'<div style="font-size:0.78rem;font-weight:600;color:#374151;margin:0.45rem 0 0.2rem;">{title}</div>'
                    f'<div style="font-size:0.65rem;color:#9aa0ad;line-height:1.55;">{desc}</div></div>',
                    unsafe_allow_html=True
                )

        hr()

        if st.session_state.context_result:
            r = st.session_state.context_result
            notice("Context database already built. Rebuild only if the codebase has changed.", "ok", "check-circle")
            m = st.columns(4)
            with m[0]: mcard("Strategy",      r["strategy"].upper(), icon_name="git-branch")
            with m[1]: mcard("Chunks Stored", f"{r['total_chunks']:,}", "vectors", icon_name="layers")
            with m[2]: mcard("DB Size",        f"{r['vector_db_size_mb']} MB", "local", icon_name="hard-drive")
            with m[3]: mcard("LOC Indexed",    f"{r['total_loc']:,}", icon_name="code-2")
            st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
            if st.button("View Project Status →", key="go3a"): go(3); st.rerun()
        else:
            notice("Runs entirely on your machine. No internet required. Expect 1–5 min depending on CPU.", "info", "info")
            if st.button("Build Context Database", key="build_ctx"):
                bar = st.progress(0, text="Initializing...")
                for pct, msg in [
                    (8,  "Filtering — removing noise files..."),
                    (26, "Chunking — 500-token segments..."),
                    (56, "Embedding — generating vectors (longest step)..."),
                    (83, "Storing — upserting to ChromaDB..."),
                    (95, "Finalizing..."),
                ]:
                    time.sleep(0.4); bar.progress(pct, text=msg)
                data, err = api_call("post", "/context/build",
                                     json={"project_id": st.session_state.project_id})
                bar.progress(100, text="Complete.")
                if err:
                    notice(f"Context build failed — {err}", "error", "alert-circle")
                else:
                    st.session_state.context_result = data
                    notice("Vector database built successfully. Ready for section generation.", "ok", "check-circle")
                    m = st.columns(4)
                    with m[0]: mcard("Strategy",      data["strategy"].upper(), icon_name="git-branch")
                    with m[1]: mcard("Chunks Stored", f"{data['total_chunks']:,}", icon_name="layers")
                    with m[2]: mcard("DB Size",        f"{data['vector_db_size_mb']} MB", icon_name="hard-drive")
                    with m[3]: mcard("LOC Indexed",    f"{data['total_loc']:,}", icon_name="code-2")
                    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
                    if st.button("View Project Status →", key="go3b"): go(3); st.rerun()

    with right:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        slabel("Confirmed Sections")
        if st.session_state.confirmed_sections:
            for s in st.session_state.confirmed_sections:
                st.markdown(
                    f'<span class="cbadge" style="display:block;margin-bottom:0.3rem;">{s}</span>',
                    unsafe_allow_html=True
                )
        else:
            st.markdown(
                '<div style="font-size:0.73rem;color:#c4c9d4;">None confirmed yet.</div>',
                unsafe_allow_html=True
            )


# ══════════════════════════════════════════════════════
# PAGE 3 — GENERATION
# ══════════════════════════════════════════════════════
elif cur == 3:
    if not st.session_state.project_id:
        notice("No project loaded — complete Step 01 first.", "error", "alert-circle")
        if st.button("Back to Ingest"): go(0); st.rerun()
        st.stop()
    if not st.session_state.confirmed_sections:
        notice("No sections confirmed — complete Step 02 first.", "warn", "alert-triangle")
        if st.button("Back to Sections"): go(1); st.rerun()
        st.stop()
    if not st.session_state.context_result:
        notice("Context not built — complete Step 03 first.", "warn", "alert-triangle")
        if st.button("Back to Context"): go(2); st.rerun()
        st.stop()

    ph_ico = lucide("file-text", 20, "%234f6ef7")
    st.markdown(
        f'<div class="page-head">'
        f'<div class="page-head-title">{ph_ico} Section Generation</div>'
        f'<div class="page-head-sub">Each confirmed section is generated individually using only the most '
        f'relevant code chunks retrieved from ChromaDB. Sections scoring below 0.7 are automatically '
        f'regenerated once with an improved prompt.</div></div>',
        unsafe_allow_html=True
    )

    pid      = st.session_state.project_id
    sections = st.session_state.confirmed_sections
    total    = len(sections)

    # ── Start generation
    if not st.session_state.get("generation_started"):
        notice(
            f"Ready to generate <strong>{total} sections</strong>. "
            "This runs on Groq — expect ~10–30 seconds per section.",
            "info", "info"
        )
        if st.button("Start Generation", key="start_gen"):
            data, err = api_call("post", f"/generate/start/{pid}")
            if err:
                notice(f"Failed to start generation — {err}", "error", "alert-circle")
            else:
                st.session_state.generation_started = True
                st.rerun()
        st.stop()

    # ── Poll status
    status_data, err = api_call("get", f"/generate/status/{pid}")
    if err:
        notice(f"Could not fetch generation status — {err}", "error", "alert-circle")
        st.stop()

    finished    = status_data["finished"]
    completed   = status_data["completed"]
    in_progress = status_data["in_progress"]
    sec_states  = status_data["sections"]

    # ── Progress bar
    progress_pct = completed / total if total > 0 else 0
    prog_label   = f"Generating... {completed} of {total} complete" if not finished else f"All {total} sections complete"
    st.progress(progress_pct, text=prog_label)

    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

    # ── Section status cards
    slabel("Section Progress")
    for section_name in sections:
        s     = sec_states.get(section_name, {})
        state = s.get("status", "pending")
        score = s.get("quality_score")
        regen = s.get("regenerated", False)
        is_ip = (section_name == in_progress)

        # Colors and icons per state
        if is_ip or state == "in_progress":
            border = "#c7d4fd"; bg = "#f5f7ff"; ico_name = "loader"; ico_color = "%234f6ef7"
            state_label = '<span class="badge badge-blue">Generating...</span>'
        elif state == "success":
            border = "#b9e8ce"; bg = "#f0faf5"; ico_name = "check-circle"; ico_color = "%231a7a46"
            state_label = f'<span class="badge badge-green">✓ {score}</span>'
        elif state == "low_quality":
            border = "#fde68a"; bg = "#fffceb"; ico_name = "alert-triangle"; ico_color = "%23b45309"
            state_label = f'<span class="badge badge-amber">⚠ {score}</span>'
        elif state == "failed":
            border = "#fecaca"; bg = "#fff5f5"; ico_name = "x-circle"; ico_color = "%23b91c1c"
            state_label = '<span class="badge badge-red">Failed</span>'
        else:
            border = "#e8eaed"; bg = "#fafafa"; ico_name = "clock"; ico_color = "%23c4c9d4"
            state_label = '<span class="badge badge-gray">Pending</span>'

        regen_badge = (
            '<span class="badge badge-amber" style="margin-left:0.4rem;">↻ Regenerated</span>'
            if regen else ""
        )
        s_ico = lucide(ico_name, 14, ico_color)

        st.markdown(
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'padding:0.7rem 1rem;border-radius:8px;border:1px solid {border};'
            f'background:{bg};margin-bottom:0.3rem;">'
            f'<div style="display:flex;align-items:center;gap:0.65rem;">'
            f'{s_ico}<span style="font-size:0.82rem;font-weight:500;color:#374151;">{section_name}</span>'
            f'</div>'
            f'<div>{state_label}{regen_badge}</div></div>',
            unsafe_allow_html=True
        )

    # ── Auto-refresh while in progress
        if not finished:
            import time
            time.sleep(3)
            st.rerun()
    else:
        st.session_state.generation_finished = True

        # Fetch full section contents once and store for Assembly
        if not st.session_state.get("generation_results"):
            results_data, results_err = api_call("get", f"/generate/results/{pid}")
            if not results_err and results_data:
                st.session_state.generation_results = results_data.get("sections", [])

        success_count = sum(1 for s in sec_states.values() if s["status"] == "success")
        low_count     = sum(1 for s in sec_states.values() if s["status"] == "low_quality")
        failed_count  = sum(1 for s in sec_states.values() if s["status"] == "failed")
        avg_score     = (
            sum(s["quality_score"] for s in sec_states.values() if s["quality_score"] is not None)
            / max(total, 1)
        )

        st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)
        notice(f"Generation complete. {success_count} succeeded · {low_count} low quality · {failed_count} failed.", "ok", "check-circle")

        mc = st.columns(4)
        with mc[0]: mcard("Total Sections", str(total),         icon_name="file-text")
        with mc[1]: mcard("Succeeded",      str(success_count), icon_name="check-circle")
        with mc[2]: mcard("Avg Quality",    f"{avg_score:.2f}", icon_name="bar-chart-2")
        with mc[3]: mcard("Regenerated",    str(sum(1 for s in sec_states.values() if s["regenerated"])), icon_name="refresh-cw")

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        if st.button("Continue to Assembly →", key="go4"):
            go(4); st.rerun()



elif cur == 4:
    if not st.session_state.project_id:
        notice("No project loaded — complete Step 01 first.", "error", "alert-circle")
        if st.button("← Ingest"): go(0); st.rerun()
        st.stop()

    if not st.session_state.confirmed_sections:
        notice("No sections confirmed — complete Step 02 first.", "warn", "alert-triangle")
        if st.button("← Sections"): go(1); st.rerun()
        st.stop()

    # ── Auto-fetch results from backend if not already in session state
    if not st.session_state.get("generation_results"):
        results_data, results_err = api_call("get", f"/generate/results/{st.session_state.project_id}")
        if not results_err and results_data:
            sections = results_data.get("sections", [])
            sections_with_content = [s for s in sections if s.get("content", "").strip()]
            if sections_with_content:
                st.session_state.generation_results = sections_with_content

    gen_results = st.session_state.get("generation_results", [])

    left, right = st.columns([18, 7], gap="large")

    with left:
        ph_ico = lucide("book-open", 20, "%234f6ef7")
        st.markdown(
            f'<div class="page-head">'
            f'<div class="page-head-title">{ph_ico} Document Assembly</div>'
            f'<div class="page-head-sub">All generated sections are merged in order into a professional '
            f'<code style="background:#f1f3f5;color:#374151;padding:0.1rem 0.3rem;border-radius:3px;font-size:0.77rem;">.docx</code> '
            f'with title page, table of contents, headers, footers, and page numbers.</div></div>',
            unsafe_allow_html=True
        )

        # ── Already assembled
        if st.session_state.get("assembly_result"):
            r = st.session_state.assembly_result
            notice("Document assembled successfully. Download it below.", "ok", "check-circle")

            mc = st.columns(3)
            with mc[0]: mcard("Word Count", f"{r['word_count']:,}", "words",  "", "file-text")
            with mc[1]: mcard("Est. Pages", str(r["page_estimate"]), "pages", "", "book-open")
            with mc[2]: mcard("Sections",   str(r["section_count"]), "merged","", "layers")

            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            slabel("Section Order")
            for i, sec in enumerate(sorted(gen_results, key=lambda s: s.get("order", i))):
                qs        = sec.get("quality_score", 0) or 0
                badge_cls = "badge-green" if qs >= 0.7 else "badge-amber" if qs >= 0.5 else "badge-red"
                wc        = len(sec.get("content", "").split())
                st.markdown(
                    f'<div class="card" style="display:flex;justify-content:space-between;align-items:center;padding:0.7rem 1rem;">'
                    f'<div style="display:flex;align-items:center;gap:0.6rem;">'
                    f'<span style="font-size:0.65rem;color:#9aa0ad;font-weight:700;width:20px;">{i+1:02d}</span>'
                    f'<span style="font-size:0.82rem;font-weight:600;color:#374151;">{sec["name"]}</span></div>'
                    f'<div style="display:flex;align-items:center;gap:0.6rem;">'
                    f'<span style="font-size:0.68rem;color:#9aa0ad;">{wc:,} words</span>'
                    f'<span class="badge {badge_cls}">{int(qs * 100)}%</span></div></div>',
                    unsafe_allow_html=True
                )

            st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
            docx_path = r["file_path"]
            try:
                with open(docx_path, "rb") as f:
                    st.download_button(
                        label="⬇  Download .docx",
                        data=f.read(),
                        file_name=f"{st.session_state.metadata.get('project_name', 'document').replace(' ', '_')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                    )
            except FileNotFoundError:
                notice(f"File not found at {docx_path}. Re-assemble.", "error", "alert-circle")

            st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
            if st.button("Continue to Review →", key="go5", use_container_width=True):
                go(5); st.rerun()

        else:
            # ── Pre-assembly state
            if not gen_results:
                notice(
                    "No generated sections found — complete Phase 3 (Section Generation) first. "
                    "If generation already ran, the server may have restarted and lost the in-memory state. "
                    "Go back to Phase 3 and re-run generation.",
                    "warn", "alert-triangle"
                )
                if st.button("← Back to Generation", key="back_to_gen"):
                    go(3); st.rerun()
            else:
                slabel(f"{len(gen_results)} sections ready to assemble")
                for i, sec in enumerate(sorted(gen_results, key=lambda s: s.get("order", i))):
                    wc = len(sec.get("content", "").split())
                    st.markdown(
                        f'<div class="card" style="display:flex;justify-content:space-between;align-items:center;padding:0.65rem 1rem;">'
                        f'<div style="display:flex;align-items:center;gap:0.6rem;">'
                        f'<span style="font-size:0.65rem;color:#9aa0ad;font-weight:700;width:20px;">{i+1:02d}</span>'
                        f'<span style="font-size:0.82rem;font-weight:500;color:#374151;">{sec["name"]}</span></div>'
                        f'<span style="font-size:0.68rem;color:#9aa0ad;">{wc:,} words</span></div>',
                        unsafe_allow_html=True
                    )

                st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

                if st.button("Assemble Document", key="btn_assemble", use_container_width=True):
                    bar = st.progress(0, text="Preparing sections...")
                    for pct, msg in [
                        (20, "Rendering title page..."),
                        (45, "Generating table of contents..."),
                        (65, "Formatting sections..."),
                        (85, "Adding headers & footers..."),
                        (95, "Saving .docx..."),
                    ]:
                        time.sleep(0.35)
                        bar.progress(pct, text=msg)

                    payload = {
                        "project_id": st.session_state.project_id,
                        "metadata":   st.session_state.metadata,
                        "sections":   gen_results,
                    }
                    data, err = api_call("post", f"/api/assemble/{st.session_state.project_id}", json=payload)
                    bar.progress(100, text="Done.")

                    if err:
                        notice(f"Assembly failed: {err}", "error", "alert-circle")
                    else:
                        st.session_state.assembly_result = data
                        notice("Document assembled successfully!", "ok", "check-circle")
                        st.rerun()

    with right:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        slabel("What's included")
        for ico, lbl in [
            ("file-text", "Title page — name, client, team, date"),
            ("list",      "Auto table of contents"),
            ("type",      "H1 / H2 / H3 heading hierarchy"),
            ("code",      "Monospace code blocks"),
            ("table",     "Tables for APIs & tech stack"),
            ("bookmark",  "Page numbers + headers/footers"),
        ]:
            st.markdown(
                f'<div class="stat-row">'
                f'<div class="stat-label">{lucide(ico, 11, "%239aa0ad")}&nbsp;{lbl}</div></div>',
                unsafe_allow_html=True
            )



# ══════════════════════════════════════════════════════
# PAGE 5 — STATUS
# ══════════════════════════════════════════════════════
elif cur == 5:
    if not st.session_state.project_id:
        fo_ico = lucide("folder-open", 36, "%23d1d5db")
        st.markdown(
            f'<div class="card" style="text-align:center;padding:4.5rem 2rem;">'
            f'{fo_ico}<div style="font-size:0.86rem;color:#9aa0ad;margin-top:1.2rem;">'
            f'No project loaded — complete Step 01 to begin.</div></div>',
            unsafe_allow_html=True
        )
        if st.button("Go to Ingest"): go(0); st.rerun()
        st.stop()

    meta  = st.session_state.metadata
    an    = st.session_state.analysis or {}
    pname = meta.get("project_name", "Unnamed Project")
    cl    = meta.get("client_name", "—")
    team  = meta.get("team_members") or []
    tstr  = ", ".join(team) if team else "—"
    desc  = meta.get("description", "")
    pid   = st.session_state.project_id or ""

    left, right = st.columns([17, 6], gap="large")

    with left:
        ph_ico = lucide("layout-dashboard", 20, "%234f6ef7")
        st.markdown(
            f'<div class="page-head">'
            f'<div class="page-head-title">{ph_ico} Project Status</div>'
            f'<div class="page-head-sub">Full pipeline overview. Phases 1–3 reflect your current progress. '
            f'Phases 4–8 unlock in upcoming releases.</div></div>',
            unsafe_allow_html=True
        )

        st.markdown(
            f'<div class="card-blue" style="margin-bottom:1.5rem;">'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;">'
            f'<div style="flex:1;min-width:0;">'
            f'<div style="font-size:1.1rem;font-weight:700;color:#111318;letter-spacing:-0.025em;margin-bottom:0.25rem;">{pname}</div>'
            f'<div style="font-size:0.72rem;color:#6b8af0;margin-bottom:0.2rem;">Client: {cl}&nbsp;&nbsp;·&nbsp;&nbsp;Team: {tstr}</div>'
            f'<div style="font-size:0.71rem;color:#9aa0ad;max-width:500px;line-height:1.65;">{desc}</div>'
            f'</div><div style="font-family:monospace;font-size:0.58rem;color:#b0bcf8;flex-shrink:0;">{pid}</div>'
            f'</div></div>',
            unsafe_allow_html=True
        )

        slabel("Pipeline")
        PHASES = [
            ("upload-cloud",  "Phase 1", "Ingest & Analyze",   bool(an)),
            ("list-checks",   "Phase 2", "Section Selection",  bool(st.session_state.confirmed_sections)),
            ("database",      "Phase 3", "Context Building",   bool(st.session_state.context_result)),
            ("file-text",     "Phase 4", "Section Generation", False),
            ("book-open",     "Phase 5", "Document Assembly",  False),
            ("user-check",    "Phase 6", "Human Review",       False),
            ("send",          "Phase 7", "Publishing",         False),
            ("bar-chart-2",   "Phase 8", "Output & Reporting", False),
        ]
        for ico_name, ph, name, done_ph in PHASES:
            state = "done" if done_ph else "locked"
            p_ico = lucide(ico_name, 11, "%231a7a46" if done_ph else "%23c4c9d4")
            badge = ('<span class="badge badge-green" style="margin-left:auto;">Complete</span>'
                     if done_ph else
                     '<span class="badge badge-gray" style="margin-left:auto;">Pending</span>')
            st.markdown(
                f'<div class="pline pline-{state}">'
                f'<div class="pline-dot pline-dot-{state}">{p_ico}</div>'
                f'<div class="pline-phase">{ph}</div>'
                f'<div class="pline-name pline-name-{state}">{name}</div>'
                f'{badge}</div>',
                unsafe_allow_html=True
            )

        if an:
            hr()
            slabel("Codebase Analysis")
            mc = st.columns(4)
            with mc[0]: mcard("Total LOC",     f"{an.get('total_loc',0):,}", icon_name="code-2")
            with mc[1]: mcard("API Endpoints", str(an.get("api_endpoints_count", 0)), icon_name="network")
            with mc[2]: mcard("Dockerfile",    "Yes" if an.get("has_dockerfile") else "No", icon_name="container")
            with mc[3]: mcard("CI / CD",       "Yes" if an.get("has_cicd") else "No", icon_name="git-merge")

            LBL2 = "font-size:0.6rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#9aa0ad;margin:0.75rem 0 0.4rem;"
            tc = st.columns(3)
            for col, key, lbl in zip(tc, ["languages","frameworks","databases"], ["Languages","Frameworks","Databases"]):
                with col:
                    st.markdown(f'<div style="{LBL2}">{lbl}</div>', unsafe_allow_html=True)
                    tagrow(an.get(key) or [])

        if st.session_state.confirmed_sections:
            hr()
            slabel(f"Confirmed Sections — {len(st.session_state.confirmed_sections)}")
            st.markdown(
                "".join(f'<span class="cbadge">{s}</span>' for s in st.session_state.confirmed_sections),
                unsafe_allow_html=True
            )

        if st.session_state.context_result:
            hr()
            slabel("Context Database")
            r  = st.session_state.context_result
            rm = st.columns(3)
            with rm[0]: mcard("Chunks Stored", f"{r['total_chunks']:,}", icon_name="layers")
            with rm[1]: mcard("DB Size",        f"{r['vector_db_size_mb']} MB", icon_name="hard-drive")
            with rm[2]: mcard("Strategy",       r["strategy"].upper(), icon_name="git-branch")

    with right:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        slabel("Quick Actions")
        if not an:
            if st.button("Start Ingest", use_container_width=True): go(0); st.rerun()
        elif not st.session_state.confirmed_sections:
            if st.button("Select Sections", use_container_width=True): go(1); st.rerun()
        elif not st.session_state.context_result:
            if st.button("Build Context", use_container_width=True): go(2); st.rerun()
        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
        if st.button("New Project", use_container_width=True, key="qa_reset"):
            for k, v in DEFAULTS.items(): st.session_state[k] = v
            st.rerun()

        st.markdown("<div style='height:0.9rem'></div>", unsafe_allow_html=True)
        slabel("Coming Next")
        upcoming = [
            ("file-text",  "Section Generation", "Phase 4"),
            ("book-open",  "Document Assembly",  "Phase 5"),
            ("user-check", "Human Review",        "Phase 6"),
            ("send",       "Publishing",          "Phase 7"),
        ]
        for ico_name, lbl, ph in upcoming:
            up_ico = lucide(ico_name, 11, "%23c4c9d4")
            st.markdown(
                f'<div class="stat-row">'
                f'<div class="stat-label">{up_ico}&nbsp;{lbl}</div>'
                f'<div style="font-size:0.62rem;color:#c4c9d4;">{ph}</div></div>',
                unsafe_allow_html=True
            )
