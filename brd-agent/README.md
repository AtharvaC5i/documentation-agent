# BRD Generation Agent

AI-powered Business Requirements Document generator. Takes meeting transcripts and user stories as input, extracts a structured Requirements Pool, detects conflicts, generates all BRD sections via Databricks LLMs, and produces a professional Word document.

---

## Architecture Overview

```
Frontend (React)  ──→  Backend (FastAPI)  ──→  Databricks Model Serving
     ↑                      │                        (LLM calls)
     │                      ↓
     └──────────  Requirements Pool (in-memory)
                            │
                            ↓
                     Word Document (.docx)
```

### Key Files

```
brd-agent/
├── backend/
│   ├── main.py                        # FastAPI app, all API routes
│   ├── requirements.txt               # Python dependencies
│   ├── .env.example                   # Copy to .env and fill in credentials
│   ├── models/
│   │   └── project.py                 # Project & Requirement data models
│   ├── pipelines/
│   │   ├── extraction_pipeline.py     # Transcript normalization + requirement extraction
│   │   ├── generation_pipeline.py     # BRD section generation with quality scoring
│   │   └── document_pipeline.py       # Word .docx assembly
│   ├── agents/
│   │   ├── conflict_detector.py       # Contradiction and gap detection
│   │   ├── section_suggester.py       # AI section recommendation
│   │   └── section_prompts.py         # Section-specific LLM prompts (all 19 sections)
│   └── utils/
│       ├── databricks_client.py       # Databricks API calls + JSON parsing
│       ├── file_utils.py              # Upload/output path management
│       └── env_loader.py              # .env file loading
├── frontend/
│   ├── package.json
│   └── src/
│       ├── App.js                     # Router
│       ├── index.css                  # Global styles
│       ├── utils/api.js               # All API calls
│       ├── hooks/usePolling.js        # Polling hook for async tasks
│       ├── components/
│       │   ├── Layout.js              # Sidebar + topbar shell
│       │   ├── StepIndicator.js       # 7-step progress indicator
│       │   ├── ProgressCard.js        # Live progress display
│       │   └── QualityBadge.js        # Quality score display
│       └── pages/
│           ├── Home.js                # Dashboard + recent projects
│           ├── QuestionBank.js        # Pre-meeting question guide
│           ├── NewProject.js          # Project creation form
│           ├── Upload.js              # File upload + synthetic data
│           ├── Extraction.js          # Live extraction progress + pool preview
│           ├── ConflictResolution.js  # Conflict review + gap coverage map
│           ├── SectionSelection.js    # AI-suggested section checklist
│           ├── Generation.js          # Live section generation progress
│           ├── Review.js              # Human review with approve/regenerate
│           └── Complete.js            # Download + generation report
└── synthetic_data/
    ├── transcript.txt                 # ShopEase e-commerce discovery call (45 min)
    ├── user_stories.txt               # 25 user stories for ShopEase
    └── question_bank.json             # Pre-meeting question bank (11 sections, 50+ questions)
```

---

## Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+
- A Databricks workspace with Model Serving enabled
- A served model endpoint (e.g. `databricks-meta-llama-3-3-70b-instruct`)

---

### Step 1 — Databricks Setup

1. Log in to your Databricks workspace
2. Go to **Machine Learning → Serving**
3. Click **Create serving endpoint**
4. Select a foundation model (recommended: Meta Llama 3.3 70B Instruct)
5. Note down the **endpoint name** (e.g. `databricks-meta-llama-3-3-70b-instruct`)
6. Go to **Settings → User Settings → Access Tokens**
7. Click **Generate New Token** and copy it

---

### Step 2 — Backend Setup

```bash
# Navigate to backend directory
cd brd-agent/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
# OR
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
```

Edit `.env` and fill in your values:
```env
DATABRICKS_HOST=https://your-workspace.azuredatabricks.net
DATABRICKS_TOKEN=dapi_your_token_here
DATABRICKS_MODEL_ENDPOINT=databricks-meta-llama-3-3-70b-instruct
```

Start the backend:
```bash
# From the backend/ directory
python main.py
```

The API will be available at `http://localhost:8000`
API docs at `http://localhost:8000/docs`

---

### Step 3 — Frontend Setup

```bash
# Open a new terminal
cd brd-agent/frontend

# Install dependencies
npm install

# Start development server
npm start
```

The frontend will open at `http://localhost:3000`

---

### Step 4 — Using the Application

#### Flow A: Test with Synthetic Data (Recommended First)

1. Open `http://localhost:3000`
2. Click **New Project**
3. Fill in any project details (or use: "ShopEase", "RetailCorp India", "E-Commerce")
4. On the Upload page, check **"Use Synthetic Data (Demo)"**
5. Click **Start Extraction**
6. Watch the Requirements Pool build in real time
7. Review conflicts and gaps
8. Select/deselect BRD sections
9. Watch section generation with live quality scores
10. Review each section — approve or request edits with feedback
11. Click **Generate BRD Document**
12. Download the `.docx` file

#### Flow B: Pre-Meeting Question Bank

1. Click **Question Bank** in the sidebar
2. Browse questions by BRD section
3. Click **Export** to download as `.txt` for your team
4. Take this into your next client discovery call

#### Flow C: Real Project

1. Conduct your discovery call using the Question Bank guide
2. Export the transcript as `.txt` from your meeting tool
3. Export user stories from Jira/Linear as `.txt` or `.csv`
4. Create a new project and upload both files
5. Run the full pipeline

---

## Databricks Model Notes

The agent calls Databricks via the **OpenAI-compatible API** at:
```
POST {DATABRICKS_HOST}/serving-endpoints/{ENDPOINT_NAME}/invocations
```

Tested endpoints:
- `databricks-meta-llama-3-3-70b-instruct` — Best quality, recommended
- `databricks-meta-llama-3-1-70b-instruct` — Good alternative
- `databricks-dbrx-instruct` — Faster, slightly lower quality

To use a different endpoint, update `DATABRICKS_MODEL_ENDPOINT` in your `.env`.

---

## Pipeline Details

### What happens during Extraction

1. **Transcript normalization** — Removes filler words, separates speakers, segments by topic
2. **Requirement extraction** — LLM identifies functional reqs, NFRs, business rules, assumptions, constraints, stakeholder info from transcript chunks
3. **User story parsing** — Parses standard `As a / I want / So that` format plus acceptance criteria
4. **Glossary building** — Identifies terminology variations and canonicalizes them
5. **Conflict detection** — Compares requirements semantically for contradictions
6. **Gap analysis** — Maps requirement coverage to all 19 BRD sections
7. **Section suggestion** — AI recommends which sections to include based on coverage

### What happens during Generation

Each section:
1. Queries Requirements Pool for type-relevant requirements
2. Constructs a section-specific prompt (19 distinct prompts in `section_prompts.py`)
3. Sends to Databricks LLM
4. Quality scores the result (heuristic + keyword check)
5. If quality < 65% → auto-regenerates once with an improved prompt
6. Result stored with source attribution

### Quality Scoring

Quality is scored 0–1 based on:
- Content length (too short = low quality)
- Presence of structural markers (headings, tables, bullet points)
- Section-specific keyword presence (e.g. "FR-" IDs for Functional Requirements)

Scores above 80% = green, 60-80% = orange, below 60% = red and flagged for review.

---

## Extending the Project

### Adding a new BRD section type

Add a new branch in `backend/agents/section_prompts.py` under `get_section_prompt()`. Match on `section_lower` and provide a `system` and `user` prompt.

### Changing the LLM

Update `backend/utils/databricks_client.py`. The client uses the OpenAI-compatible format — any endpoint following this spec works.

### Adding database persistence

Replace `ProjectStore` in `backend/models/project.py` with a SQLAlchemy or Delta Lake implementation. The interface (`save`, `get`, `list_all`) stays the same.

### Meeting bot integration (future)

When ready to auto-transcribe calls: integrate a Zoom/Teams bot SDK, pipe audio through Whisper, and call the existing extraction pipeline with the resulting transcript. The rest of the pipeline is unchanged.

---

## Troubleshooting

**Backend won't start**
- Check Python version: `python --version` (needs 3.10+)
- Check all packages installed: `pip install -r requirements.txt`
- Check `.env` file exists in `backend/` directory

**Extraction fails / LLM errors**
- Verify `DATABRICKS_HOST` has no trailing slash
- Verify your token hasn't expired (regenerate in Databricks settings)
- Verify the endpoint name matches exactly what's in Databricks Serving
- Check endpoint is in "Ready" state in Databricks

**Frontend can't reach backend**
- Ensure backend is running on port 8000
- The frontend proxies `/api` to `localhost:8000` (configured in `package.json`)
- Check browser console for CORS errors

**Document generation fails**
- `python-docx` must be installed: `pip install python-docx`
- Check `outputs/` directory exists and is writable

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, React Router v6, Axios, react-markdown |
| Backend | FastAPI, Uvicorn, Pydantic v2 |
| LLM | Databricks Model Serving (OpenAI-compatible) |
| Document | python-docx |
| Styling | Pure CSS with CSS variables |
| Data | In-memory (ProjectStore) — swap for Delta Lake in production |
