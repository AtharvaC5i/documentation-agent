<div align="center">

# DocuFlow

**An AI documentation platform that turns raw transcripts, codebases, and requirements**  
**into structured, professional-grade documents — entirely on your infrastructure.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-339933?style=flat-square&logo=node.js&logoColor=white)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=white)](https://reactjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

</div>

---

## Overview

DocuFlow is a unified hub for **three independently deployed AI agents**, each purpose-built for a specific document type. Upload your source material, let the agent extract structure and generate content, review every section before it ships, and download a finished document — without writing a single line of documentation manually.

> **Privacy-first by design.** All LLM inference runs through **Databricks Model Serving**. The vector pipeline (chunking, embedding, storage) runs entirely on your machine. No source code or sensitive content leaves your infrastructure except the final generation prompt.

---

## Agents

| Agent                                                            | Input                     | Output                                       |  Port  |
| :--------------------------------------------------------------- | :------------------------ | :------------------------------------------- | :----: |
| [BRD Generation Agent](#-brd-generation-agent)                   | Transcripts, user stories | Business Requirements Document `.docx`       | `3000` |
| [Technical Documentation Agent](#-technical-documentation-agent) | GitHub URL, ZIP codebase  | Technical documentation `.docx` / `.pdf`     | `5174` |
| [AI Solution Architect Agent](#-ai-solution-architect-agent)     | BRDs, technical docs      | Architecture diagrams, presentations `.pptx` | `5175` |

The **DocuFlow Landing Page** runs on port `5173` and routes users to each agent.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      DocuFlow Hub                        │
│                React · Vite · Port 5173                  │
└──────────┬──────────────┬──────────────┬────────────────┘
           │              │              │
           ▼              ▼              ▼
     ┌──────────┐  ┌──────────────┐  ┌──────────────┐
     │   BRD    │  │   Tech Doc   │  │   PPT/Arch   │
     │  Agent   │  │    Agent     │  │    Agent     │
     │  :3000   │  │    :5174     │  │    :5175     │
     └────┬─────┘  └──────┬───────┘  └──────┬───────┘
          │               │                  │
          ▼               ▼                  ▼
     ┌──────────┐  ┌──────────────┐  ┌──────────────┐
     │  FastAPI │  │   FastAPI    │  │   FastAPI    │
     │  :8000   │  │    :8001     │  │    :8002     │
     └────┬─────┘  └──────┬───────┘  └──────┬───────┘
          │               │                  │
          └───────────────┼──────────────────┘
                          │
                          ▼
              ┌─────────────────────┐
              │  Databricks Model   │
              │   Serving (LLM)     │
              └─────────────────────┘
```

---

## 📄 BRD Generation Agent

Ingests meeting transcripts and user stories, extracts every business requirement, surfaces conflicts, maps coverage across 19 standard BRD sections, and assembles a professionally formatted Word document with cover page, table of contents, running headers, and styled tables.

### Pipeline

```
Transcript + User Stories
│
▼
[Transcript Cleaning]
│
├──▶ [LLM: Transcript Extraction] ──▶ Requirements Pool (~60–80 reqs)
├──▶ [LLM: User Story Extraction]
├──▶ [Python: Semantic Deduplication] ──▶ Glossary
├──▶ [LLM: Glossary + Coverage Map] ──▶ Section Coverage Map
└──▶ [LLM: Conflict Detection] ──▶ Conflict List
│
▼
[Python: Section Suggestion Rules] ──▶ Suggested Sections
│
↓ Human reviews and selects sections
│
[LLM × 15–18: Section Generation] ──▶ BRD Sections + Quality Scores
[Python: Word Count Enforcer]
│
↓ Human reviews, edits, approves
│
[python-docx: Document Assembly] ──▶ BRD.docx
```

> **Total LLM calls per full run:** ~20 (4 extraction + 15–18 section generation)  
> **Typical end-to-end time:** 8–15 minutes depending on Databricks endpoint latency

### Key Features

| Feature                         | Description                                                                         |
| :------------------------------ | :---------------------------------------------------------------------------------- |
| **Requirement extraction**      | 60–80 requirements extracted per typical project                                    |
| **Conflict detection**          | Surfaces contradictions between transcript and user stories                         |
| **19-section coverage mapping** | Identifies section gaps before generation begins                                    |
| **Section-level human review**  | Edit, approve, reject, or regenerate any section individually                       |
| **Quality scoring**             | Heuristic 0–1 score; sections below 0.60 auto-regenerate with an improved prompt    |
| **Living BRD**                  | Upload a follow-up transcript to detect changes and produce a v2                    |
| **Follow-up email**             | Auto-drafts a targeted client email for every coverage gap                          |
| **Traceability matrix**         | Links every BRD section back to its source requirement and original transcript line |
| **Pre-meeting question bank**   | 50+ questions across 11 categories for structured discovery calls                   |

### Document Output

The generated BRD targets **35–50 pages** for a typical project with 15–18 sections.

| Section                 |     Word Limit      |
| :---------------------- | :-----------------: |
| Executive Summary       |         300         |
| Functional Requirements | 500 _(table-heavy)_ |
| User Journeys           |         300         |
| Glossary                |         300         |
| All other sections      |         200         |

### Stack

| Layer             | Technology                                             |
| :---------------- | :----------------------------------------------------- |
| Frontend          | React 18, React Router v6, Axios                       |
| Backend           | FastAPI, Uvicorn, Pydantic v2                          |
| LLM               | Databricks Model Serving — Meta Llama 3.3 70B Instruct |
| Document assembly | python-docx                                            |
| Storage           | JSON files on disk _(no database required)_            |
| Styling           | Custom dark CSS design system — Plus Jakarta Sans      |

### Setup

```bash
# Backend
cd brd-agent/backend
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Fill in Databricks credentials
python main.py
# → http://localhost:8000

# Frontend
cd brd-agent/frontend
npm install
npm start
# → http://localhost:3000
```

**Required `.env` values:**

```env
DATABRICKS_HOST=https://adb-xxxxxxxxxxxx.azuredatabricks.net
DATABRICKS_TOKEN=dapi_your_token_here
DATABRICKS_MODEL_ENDPOINT=databricks-meta-llama-3-3-70b-instruct
APP_PORT=8000
APP_ENV=development
```

---

## 🔧 Technical Documentation Agent

Analyses your source code, understands your stack, retrieves the most relevant code context for each section using semantic vector search, and generates high-quality technical prose grounded in actual code — not guesswork.

### Pipeline

```
GitHub URL / ZIP Archive
│
▼
[Noise Filtering] ← Strips node_modules, build artefacts, binaries
│
▼
[Static Analysis] ← Languages, frameworks, databases, infra signals, API count
│
▼
[AI Section Suggestion] ← Recommended vs optional sections based on detected stack
│
↓ Human confirms sections
│
▼
[Chunking + Embedding] ← 500-token chunks, 50-token overlap, all-MiniLM-L6-v2 on CPU
│
├── Under 50k LOC ──▶ [Flat ChromaDB indexing]
└── Over 50k LOC  ──▶ [RAPTOR — recursive summary tree]
│
▼
[RAG Generation per section] ← Top-k chunks retrieved, sent to Databricks LLM
│
▼
[Quality Scoring] ← Sections below 0.70 auto-regenerate once
│
↓ Human reviews, edits, reorders
│
▼
[python-docx Assembly] ← Title page, TOC, headings, code blocks, tables
│
▼
.docx
```

### Key Features

| Feature                         | Description                                                                                                                                          |
| :------------------------------ | :--------------------------------------------------------------------------------------------------------------------------------------------------- |
| **RAPTOR for large codebases**  | Recursive abstractive processing enables simultaneous access to implementation details and high-level architecture context on codebases over 50k LOC |
| **Fully local vector pipeline** | ChromaDB and all-MiniLM-L6-v2 run on CPU; only generation prompts leave your machine                                                                 |
| **Grounded output**             | Every claim in the document is traceable to a specific code chunk retrieved and passed to the model                                                  |
| **Quality-enforced generation** | Sections scoring below 0.70 are automatically regenerated before the review screen                                                                   |
| **Mandatory human review**      | Approve, reject, edit inline, reorder sections, and add reviewer notes before any document is assembled                                              |
|  |

### Stack

| Layer             | Technology                                                |
| :---------------- | :-------------------------------------------------------- |
| Frontend          | Vite React, proxied via `/api-proxy`                      |
| Backend           | FastAPI, Uvicorn, Pydantic v2                             |
| Embedding model   | `all-MiniLM-L6-v2` — sentence-transformers, CPU inference |
| Vector database   | ChromaDB — local, persistent                              |
| LLM               | Databricks Model Serving                                  |
| Document assembly | python-docx                                               |

### Setup

```bash
# Backend
cd tech-doc-agent/backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 8001

# Frontend
cd tech-doc-agent/frontend
npm install
npm run dev
# → http://localhost:5174
```

**Vite proxy config** (`vite.config.js`):

```js
server: {
  port: 5174,
  proxy: {
    '/api-proxy': {
      target: 'http://localhost:8001',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api-proxy/, ''),
    },
  },
}
```

---

## 🏗️ AI Solution Architect Agent

Takes completed BRDs and technical documentation as input and transforms them into architecture diagrams, structured presentations, and production-ready outputs. Powered by Databricks Model Serving (Claude Sonnet).

### API Endpoints

| Method | Path                    | Description                          |
| :----: | :---------------------- | :----------------------------------- |
| `GET`  | `/health`               | Health check                         |
| `POST` | `/api/v1/generate`      | Submit BRD + tech doc as form text   |
| `POST` | `/api/v1/generate-file` | Submit BRD + tech doc as file upload |

### Key Features

| Feature                       | Description                                                                       |
| :---------------------------- | :-------------------------------------------------------------------------------- |
| **Flexible input**            | Accepts BRD and technical documentation as combined input via text or file upload |
| **Async pipeline**            | Long-running generation jobs handled non-blocking                                 |
| **Validated models**          | Pydantic v2 validated request and response models throughout                      |
| **Architecture-aware LLM**    | Claude Sonnet via Databricks Model Serving                                        |
| **Presentation-ready export** | `.pptx` export ready for direct stakeholder presentation                          |

### Stack

| Layer    | Technology                               |
| :------- | :--------------------------------------- |
| Frontend | Vite React, proxied via `/api`           |
| Backend  | FastAPI, Uvicorn, Pydantic v2            |
| LLM      | Databricks Model Serving — Claude Sonnet |
| Export   | `.pptx`                                  |

### Setup

```bash
# Backend
cd ppt-agent/backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 8002

# Frontend
cd ppt-agent/frontend
npm install
npm run dev
# → http://localhost:5175
```

**Vite proxy config** (`vite.config.js`):

```js
server: {
  port: 5175,
  proxy: {
    '/api': {
      target: 'http://localhost:8002',
      changeOrigin: true,
    },
  },
}
```

---

## 🌐 DocuFlow Landing Page

The hub that ties all three agents together.

```bash
cd landing-page
npm install
npm run dev
# → http://localhost:5173
```

> No backend. No proxy. A static Vite React app with Tailwind CSS that routes users to each agent via direct links. Each agent opens in a new tab so the hub stays available.

---

## 🚀 Running Everything

Open seven terminals and start each service:

```bash
# Terminal 1 — BRD Backend
cd brd-agent/backend && source venv/bin/activate && python main.py

# Terminal 2 — BRD Frontend
cd brd-agent/frontend && npm start

# Terminal 3 — Tech Doc Backend
cd tech-doc-agent/backend && source venv/bin/activate && uvicorn main:app --port 8001

# Terminal 4 — Tech Doc Frontend
cd tech-doc-agent/frontend && npm run dev

# Terminal 5 — PPT Backend
cd ppt-agent/backend && source venv/bin/activate && uvicorn main:app --port 8002

# Terminal 6 — PPT Frontend
cd ppt-agent/frontend && npm run dev

# Terminal 7 — Landing Page
cd landing-page && npm run dev
```

### Service URLs

| Service                       | URL                        |
| :---------------------------- | :------------------------- |
| Landing Page                  | http://localhost:5173      |
| BRD Agent                     | http://localhost:3000      |
| Technical Documentation Agent | http://localhost:5174      |
| AI Solution Architect Agent   | http://localhost:5175      |
| BRD API Docs                  | http://localhost:8000/docs |
| Tech Doc API Docs             | http://localhost:8001/docs |
| PPT API Docs                  | http://localhost:8002/docs |

---

## Prerequisites

| Requirement           |                   Version                    |
| :-------------------- | :------------------------------------------: |
| Python                |                3.10 or higher                |
| Node.js               |                 18 or higher                 |
| Databricks workspace  |            Model Serving enabled             |
| Served model endpoint | Ready state — Llama 3.3 70B or Claude Sonnet |

### Getting Your Databricks Credentials

1. Log in to your Databricks workspace
2. Go to **Machine Learning → Serving** — copy the exact endpoint name
3. Go to **Settings → User Settings → Developer → Access Tokens**
4. Click **Generate New Token** — copy immediately _(shown once only)_
5. Copy your workspace URL from the browser address bar

---

## Environment Variables

All three backends share the same `.env` structure:

```env
DATABRICKS_HOST=https://adb-xxxxxxxxxxxx.azuredatabricks.net
DATABRICKS_TOKEN=dapi_your_token_here
DATABRICKS_MODEL_ENDPOINT=your-endpoint-name
APP_PORT=8000
APP_ENV=development
```

---

## Troubleshooting

<details>
<summary><strong>Backend won't start</strong></summary>

```bash
python --version          # Must be 3.10+
source venv/bin/activate  # Make sure venv is active
pip install -r requirements.txt --force-reinstall
```

</details>

<details>
<summary><strong>Databricks API errors</strong></summary>

- Ensure `DATABRICKS_HOST` has no trailing slash
- Check the token hasn't expired — regenerate in **Databricks → User Settings → Access Tokens**
- Verify the endpoint name matches exactly what appears in Databricks Serving and is in **Ready** state
</details>

<details>
<summary><strong>Port already in use</strong></summary>

```bash
# macOS / Linux
lsof -i :8000 && kill -9 <PID>

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

</details>

<details>
<summary><strong>Frontend shows blank content</strong></summary>

```bash
# Hard refresh
Ctrl+Shift+R   # Windows
Cmd+Shift+R    # Mac

# Or reinstall
npm install && npm run dev
```

</details>

<details>
<summary><strong>Tech Doc — ChromaDB slow on first run</strong></summary>

Expected. The vector database is built once per project on first run and persists to disk. Subsequent runs on the same project load the existing index instantly.

</details>

---

## Tech Stack Summary

| Layer               | Technology                                                 |
| :------------------ | :--------------------------------------------------------- |
| Landing page        | React 18, Vite, Tailwind CSS                               |
| Agent frontends     | React 18, Vite _(Tech Doc, PPT)_ · React 18, CRA _(BRD)_   |
| All backends        | Python, FastAPI, Uvicorn, Pydantic v2                      |
| Embedding model     | `all-MiniLM-L6-v2` — sentence-transformers, CPU            |
| Vector database     | ChromaDB — local, persistent                               |
| LLM inference       | Databricks Model Serving _(Llama 3.3 70B · Claude Sonnet)_ |
| Document export     | python-docx                                                |
| Presentation export | `.pptx`                                                    |
| Storage             | JSON files on disk — no external database                  |

---

## License

This project is licensed under the **MIT License** — see [`LICENSE`](LICENSE) for details.
