# DocuFlow Project Architecture Analysis

**Last Updated**: May 18, 2026  
**Scope**: Three independent AI-powered documentation agents + unified landing page

---

## 1. AI SOLUTION ARCHITECT v2 (Port 5175)

### Purpose

Transforms Business Requirement Documents (BRDs) and Technical Documentation into:

- Complete solution architecture JSON (components, connections, tech stack, roadmap)
- Architecture diagrams (draw.io generated → PNG embedded in PowerPoint)
- Professional PowerPoint presentations with title slides, closing slides, and custom slides
- Structured component models with technology assignments

**Key Problem Solved**: Automates architecture design from business/technical input, eliminating manual diagram creation and architecture documentation.

---

### Main Components

| Component                | File                            | Purpose                                                                                |
| ------------------------ | ------------------------------- | -------------------------------------------------------------------------------------- |
| **FastAPI App**          | `main.py`                       | Entry point, route aggregation, CORS middleware                                        |
| **Generate Router**      | `routers/generate.py`           | HTTP endpoints for PPTX generation, file extraction, JSON regeneration                 |
| **Orchestrator Service** | `services/orchestrator.py`      | 3-step LLM pipeline orchestration                                                      |
| **Databricks Client**    | `services/databricks_client.py` | Async HTTP wrapper for Claude Sonnet via Databricks Model Serving                      |
| **PPTX Service**         | `services/pptx_service.py`      | ZIP-based PPTX merging, XML validation, slide scaling                                  |
| **Prompt Builder**       | `agents/prompt_builder.py`      | System prompts for summarization, core architecture, diagram generation, custom slides |
| **File Extractor**       | `services/file_extractor.py`    | Extracts text from PDF/DOCX/TXT/MD files                                               |
| **Response Models**      | `models/response_models.py`     | Pydantic validation for architecture JSON schema                                       |

---

### Input/Output Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: Streamlit/React UI (Port 5173)                        │
│ - BRD text input (or paste)                                     │
│ - Tech doc upload (PDF/DOCX/TXT)                                │
│ - Slide selection (template slides, custom topics)              │
└─────────────────────┬───────────────────────────────────────────┘
                      │ POST /api/v1/generate-pptx
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND: FastAPI Router → Orchestrator                          │
└─────────────────────┬───────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
    ┌─────────┐  ┌─────────┐  ┌──────────┐
    │ STEP 0  │  │ STEP 1  │  │ STEP 2   │
    │Summarize│  │ Core    │  │ Diagram  │
    │Tech Doc │  │ Arch    │  │ JSON     │
    └────┬────┘  └────┬────┘  └────┬─────┘
         │             │            │
         └─────────────┼────────────┘
                       │
        ┌──────────────▼──────────────┐
        │ LLM (Databricks Claude)     │
        │ 3 sequential API calls      │
        └──────────────┬──────────────┘
                       │
         ┌─────────────▼─────────────┐
         │ GenerateResponse JSON      │
         │ - architecture (components │
         │   + connections)           │
         │ - technology_stack         │
         │ - roadmap, risks, etc      │
         └──────────────┬─────────────┘
                        │
         ┌──────────────▼──────────────┐
         │ PPTX Service               │
         │ 1. Run Node.js script      │
         │    (generate_pptx.js)      │
         │ 2. Merge title slides      │
         │ 3. Merge closing slides    │
         │ 4. Scale/embed diagrams    │
         └──────────────┬──────────────┘
                        │
         ┌──────────────▼──────────────┐
         │ PowerPoint File (.pptx)    │
         │ Downloaded by user         │
         └───────────────────────────┘
```

### Main Processing Steps

#### **Step 0: Tech Doc Summarization** (if provided)

- **Input**: Technical documentation text (truncated to 8,000 chars)
- **LLM Call**: Invoke `SUMMARIZE_PROMPT`
- **Output**: 8-12 bullet points covering systems, APIs, data models, constraints, NFRs
- **Purpose**: Compress technical details for CORE_PROMPT input

#### **Step 1: Core Architecture Generation**

- **Input**:
  - BRD text (max 3,500 chars)
  - Tech summary array from Step 0
- **LLM Call**: Invoke `CORE_PROMPT` (strictest prompt with detailed field requirements)
- **Output**: Complete JSON containing:
  ```json
  {
    "project": { "name", "tagline", "client_context" },
    "alignment": { "goals" (5), "business_value", "success_metrics" (5) },
    "problem_statement": { "current_pain_points" (5-6), "impact", "root_cause" },
    "proposed_solution": { "summary", "key_differentiators" (5), "approach" },
    "architecture": {
      "components": [{ "id", "label", "name", "role", "technology" }] (6-8),
      "connections": [{ "from", "to", "label" }]
    },
    "data_flow": [] (6-8 steps),
    "technology_stack": { "frontend", "backend", "ai_ml", "data", "infrastructure", "security" },
    "non_functional": { "scalability", "security", "availability", "performance", "compliance" },
    "roadmap": [{ "phase", "duration", "deliverables" (4 each) }] (3 phases),
    "risks": [{ "risk", "mitigation" }] (4-5),
    "assumptions": [] (4-5),
    "open_questions": [] (4-5)
  }
  ```
- **Validation**: Pydantic models enforce structure and types

#### **Step 2: Diagram Graph Generation**

- **Input**: Architecture subset (project, architecture, technology_stack, data_flow)
- **LLM Call**: Invoke `DIAGRAM_PROMPT`
- **Output**: Simplified JSON for rendering:
  ```json
  {
    "components": [{ "id", "label", "layer" }] (5-8),
    "connections": [{ "from", "to", "label" }]
  }
  ```
- **Enrichment**: Merge with CORE_PROMPT components to add technology field
- **Purpose**: Minimal diagram JSON consumed by JavaScript renderer

#### **Step 3: PowerPoint Generation**

- **Sub-step 3a**: Run Node.js script `generate_pptx.js`
  - Receives architecture JSON
  - Renders draw.io diagrams → PNG images
  - Creates slide XML structure
  - Outputs raw PPTX bytes
- **Sub-step 3b**: Merge template slides
  - **Title Slides** (`title_slides.pptx`): Cover, TOC, Executive Summary
  - **Content Slides**: Generated from architecture data
  - **Closing Slides** (`closing_slides.pptx`): Roadmap, Q&A, Contact
  - **Process**: Uses `_safe_merge_pptx()` to append slides from templates
    - Copies only slide content (`ppt/slides/` folder)
    - Avoids corrupting masters, layouts, themes
    - Prefixes filenames to prevent ID collisions
    - Remaps internal relationship IDs

- **Sub-step 3c**: Custom slide enrichment
  - For each user-provided topic:
    - Call LLM with `CUSTOM_SLIDE_PROMPT` + topic
    - LLM returns JSON: `{ "title", "bullets": [3-6 bullets] }`
    - Append as new slide to PPTX

#### **Step 4: User Downloads PPTX**

- HTTP response with MIME type: `application/vnd.openxmlformats-officedocument.presentationml.presentation`
- Filename: `architecture.pptx`

---

### Quality Issues & Failure Modes

#### **Quality Issue 1: PowerPoint Corruption** ⚠️

**Symptom**: Windows/Office opens file and displays "Do you want to repair this presentation?"

**Root Cause** (Historical):

- Old implementation (`_zip_merge_pptx`) tried merging entire presentation structures
- Merged slide masters, layouts, themes, fonts → caused XML conflicts
- Relationship ID collisions between presentations
- Corrupted `[Content_Types].xml` due to duplicate entries

**Current Fix** (SAFE MERGE):

- New `_safe_merge_pptx()` only copies slide content (`ppt/slides/` + `ppt/media/`)
- Ignores masters, layouts, themes entirely
- Prefixes all filenames (e.g., `slide1.xml` → `m1_slide1.xml`)
- Uses `_prefix_rels_targets()` to remap internal references
- Uses `_ensure_content_type_entry()` to avoid duplicate entries
- Reorders `[Content_Types].xml` per OOXML spec (Defaults first, Overrides second)

**Mitigation**:

- ✅ Fixed in current `pptx_service.py`
- Test: Generate PPTX with title + content + closing slides → no repair dialog

#### **Quality Issue 2: Missing Components in Diagram**

**Symptom**: Diagram shows incomplete architecture (missing AI layer, data store, etc.)

**Root Cause**:

- LLM CORE_PROMPT returns fewer components than expected (6-8 required)
- DIAGRAM_PROMPT receives truncated architecture subset

**Mitigations**:

- CORE_PROMPT enforces: "architecture.components: exactly 6-8 components"
- If LLM returns fewer, frontend shows warning but still generates PPTX
- Fallback in orchestrator: if no diagram_components generated, use core components

#### **Quality Issue 3: Incomplete Tech Stack**

**Symptom**: Technology stack missing backend, database, or security technologies

**Root Cause**:

- Sparse input BRD/tech doc with limited technology details
- LLM struggles to "infer" reasonable tech choices

**Mitigations**:

- CORE_PROMPT: "fill ALL 6 layers with real tech names from the input"
- If input lacks tech details, quality score reflects this
- User can regenerate with more detailed input

#### **Quality Issue 4: Diagram XML Validation Errors**

**Symptom**: Generated PNG images don't embed in PPTX, or rendered as broken images

**Root Cause**:

- JavaScript render engine fails to create valid PNG
- PPTX XML has invalid media references
- Relationship IDs mismatch between slide XML and `_rels/slide*.xml.rels`

**Mitigations**:

- `pptx_service.py` validates XML using `etree.XMLParser(recover=True)`
- `_remap_xml_rid_references()` fixes broken relationship IDs
- `_ensure_content_type_entry()` registers media files in content types
- Fallback: if image embed fails, skip image rather than crash

#### **Quality Issue 5: LLM Timeout or Rate Limiting**

**Symptom**: PPTX generation fails after 30 seconds, no response returned

**Root Cause**:

- Databricks endpoint slow or overloaded
- 3 sequential LLM calls = 3× timeout risk
- No retry logic on Databricks client

**Mitigations**:

- Async/await pattern allows cancellation after timeout
- If Step 0 fails (summarization), continue with empty tech_summary
- If Step 1 fails (core), return 400 Bad Request with error detail
- No automatic retry (to avoid rate-limit cascades)

#### **Quality Issue 6: Custom Slide Topic Too Vague**

**Symptom**: Custom slide has generic, unhelpful bullets

**Root Cause**:

- User provides topic like "Implementation Strategy" with minimal BRD context
- LLM struggles to generate specific bullets without detailed input

**Mitigations**:

- Custom slide prompt: "Reference actual details from the BRD/tech doc"
- Enforces 3-6 bullets (not 1-2 generic ones)
- User can regenerate with better BRD input

---

### Success/Failure Modes

#### **Success Mode 1: Full Input (BRD + Tech Doc)**

✅ **Expected Output**:

- 3-step pipeline completes in ~15-20 seconds
- All architecture fields populated
- Diagram renders with 6-8 components and connections
- PPTX with title, content, closing, custom slides
- **Quality**: High — all LLM outputs well-constrained

#### **Success Mode 2: BRD Only**

✅ **Expected Output**:

- Step 0 skipped (no tech doc to summarize)
- CORE_PROMPT infers reasonable tech stack from BRD
- Diagram less technically detailed but still valid
- PPTX generated successfully
- **Quality**: Medium — relies on LLM inference

#### **Success Mode 3: Custom Slides**

✅ **Expected Output**:

- Each custom topic generates LLM call + embedded slide
- Bullets are specific and actionable
- **Quality**: Depends on BRD richness

#### **Failure Mode 1: Empty Input**

❌ **Trigger**: User submits empty BRD and empty tech doc

- **Result**: HTTP 400 Bad Request with message: "At least one of BRD text or Technical Documentation is required"
- **Recovery**: User must provide input and resubmit

#### **Failure Mode 2: BRD Too Short**

⚠️ **Trigger**: BRD is <100 characters

- **Result**: Core architecture generated but with placeholder values (missing components, generic tech stack)
- **Quality Score**: Low (user warned in frontend)
- **Recovery**: User can submit richer BRD

#### **Failure Mode 3: LLM Returns Invalid JSON**

❌ **Trigger**: DATABRICKS LLM returns malformed JSON or truncated response

- **Result**: `json.loads()` fails in orchestrator → HTTP 500 Internal Server Error
- **Message**: "Failed to parse LLM response"
- **Recovery**: User retries (LLM may succeed next time)

#### **Failure Mode 4: PPTX Merge Corruption**

❌ **Trigger**: `_safe_merge_pptx()` encounters:

- Missing slide relationships
- Invalid XML in template PPTX files
- Filename conflicts between templates
- **Result**: Exception raised, HTTP 500
- **Message**: "PowerPoint generation failed: [error detail]"
- **Recovery**: Check template PPTX files (`title_slides.pptx`, `closing_slides.pptx`) for corruption

#### **Failure Mode 5: Node.js Script Not Found**

❌ **Trigger**: `generate_pptx.js` missing or `node` command unavailable

- **Result**: `subprocess.run()` fails to find command
- **Message**: "node: command not found" or "FileNotFoundError: [Errno 2] No such file"
- **Recovery**: Ensure Node.js installed and `pptx_gen/generate_pptx.js` exists

---

## 2. BRD GENERATION AGENT (Port 3000)

### Purpose

Transforms meeting transcripts and user stories into a professional Business Requirements Document (`.docx`):

- Extracts requirements from unstructured narrative
- Deduplicates and clusters requirements semantically
- Detects conflicts and coverage gaps
- Generates 15-18 structured BRD sections
- Enables human review, editing, and approval at every step
- Creates "Living BRD" with version control and change detection

**Key Problem Solved**: Eliminates manual BRD authoring; captures requirements from meetings automatically, then surfaces ambiguities/conflicts for human decision-making.

---

### Main Components

| Component               | File                               | Purpose                                                                         |
| ----------------------- | ---------------------------------- | ------------------------------------------------------------------------------- |
| **FastAPI App**         | `main.py`                          | Entry point, CORS middleware, dependency injection                              |
| **File Store**          | `storage/file_store.py`            | Persistent project storage (JSON files on disk)                                 |
| **Extraction Pipeline** | `pipelines/extraction_pipeline.py` | 4 LLM calls: transcript cleaning, extraction, story parsing, conflict detection |
| **Generation Pipeline** | `pipelines/generation_pipeline.py` | Per-section generation with quality scoring & word count enforcement            |
| **Document Pipeline**   | `pipelines/document_pipeline.py`   | Python calls Node.js `docx.js` to build Word document                           |
| **Project Model**       | `models/project.py`                | Pydantic schema for project state (requirements, sections, versioning)          |
| **Section Suggester**   | `agents/section_suggester.py`      | Rule-based system to suggest BRD sections based on coverage                     |
| **Section Prompts**     | `agents/section_prompts.py`        | Customized LLM prompts for each of 19 BRD sections                              |
| **Databricks Client**   | `utils/databricks_client.py`       | Async wrapper for Claude via Databricks Model Serving                           |
| **Living BRD Features** | `features/living_brd.py`           | Change detection, version tracking                                              |
| **Traceability**        | `features/traceability.py`         | Maps requirements → sections for audit trail                                    |

---

### Input/Output Flow

```
┌──────────────────────────────────────────────────────────────────┐
│ FRONTEND: React UI (Port 3000)                                   │
│ [1] Upload transcript (.txt)                                     │
│ [2] Upload user stories (.txt)                                   │
│ [3] Enter project metadata (name, client, industry, team)        │
│ [4] Review extracted requirements                                │
│ [5] Select BRD sections to generate                              │
│ [6] Review & edit each section                                   │
│ [7] Approve and download BRD.docx                                │
└────────────────────────┬─────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│POST /project │ │POST /ingest  │ │POST /sections│
│/create       │ │/transcript   │ │/suggest      │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       │                ▼                │
       │        ┌────────────────────┐   │
       │        │ Extraction         │   │
       │        │ Pipeline           │   │
       │        │ ┌────────────────┐ │   │
       │        │ │1. Clean        │ │   │
       │        │ │   transcript   │ │   │
       │        │ ├────────────────┤ │   │
       │        │ │2. Extract      │ │   │
       │        │ │   requirements │ │   │
       │        │ ├────────────────┤ │   │
       │        │ │3. Parse user   │ │   │
       │        │ │   stories      │ │   │
       │        │ ├────────────────┤ │   │
       │        │ │4. Deduplicate  │ │   │
       │        │ │5. Detect       │ │   │
       │        │ │   conflicts    │ │   │
       │        │ └────────────────┘ │   │
       │        └────────┬───────────┘   │
       │                 │                │
       │    ┌────────────▼────────────┐   │
       │    │LLM (Databricks)         │   │
       │    │4 sequential calls       │   │
       │    └────────────┬────────────┘   │
       │                 │                │
       └─────────────────┼────────────────┘
                         │
         ┌───────────────▼───────────────┐
         │ Project State (in memory)      │
         │ - requirements_pool (60-80)    │
         │ - glossary                     │
         │ - conflicts, gaps              │
         │ - suggested sections           │
         └───────────────┬───────────────┘
                         │
         ┌───────────────▼───────────────┐
         │ User selects sections         │
         │ (e.g., "Overview",            │
         │  "Requirements", "Roadmap")   │
         └───────────────┬───────────────┘
                         │
         ┌───────────────▼───────────────┐
         │ Generation Pipeline           │
         │ (for each section)             │
         │ ┌──────────────────────────┐  │
         │ │1. Build LLM prompt       │  │
         │ │2. Call LLM               │  │
         │ │3. Score quality (>60%)   │  │
         │ │4. Enforce word count     │  │
         │ │5. Store section         │  │
         │ └──────────────────────────┘  │
         └───────────────┬───────────────┘
                         │
         ┌───────────────▼───────────────┐
         │ Document Pipeline             │
         │ (docx.js backend)             │
         │ ┌──────────────────────────┐  │
         │ │1. Serialize sections     │  │
         │ │   to JSON                │  │
         │ │2. Call Node.js           │  │
         │ │3. Build Word document    │  │
         │ │4. Add styling, TOC,      │  │
         │ │   headers, footers       │  │
         │ └──────────────────────────┘  │
         └───────────────┬───────────────┘
                         │
         ┌───────────────▼───────────────┐
         │ File Store                    │
         │ Persist to disk:              │
         │ /outputs/BRD_{name}_v{#}.docx│
         └───────────────┬───────────────┘
                         │
         ┌───────────────▼───────────────┐
         │ User Downloads .docx          │
         └───────────────────────────────┘
```

### Main Processing Steps

#### **Phase 1: Ingestion & Extraction**

##### Step 1a: Transcript Cleaning (Python-only, no LLM call)

- **Input**: Raw transcript text (often contains filler words, speaker labels, stuttering)
- **Cleaning Rules**:
  - Remove filler words (um, uh, you know, like I said, basically, etc.)
  - Remove repeated words (`the the` → `the`)
  - Collapse multiple spaces to single space
  - Strip/join lines
- **Output**: Cleaned transcript (typically 30-40% shorter)
- **Cost**: 0 LLM calls (Python regex)

##### Step 1b: LLM Requirement Extraction from Transcript

- **Input**: Cleaned transcript (max length enforced)
- **Prompt**: "Extract all functional, non-functional, and business requirements"
- **LLM Output**: JSON array of 30-50 requirements, each with:
  - `description`: 1-2 sentences
  - `type`: "functional" | "non_functional" | "business"
  - `priority`: "must_have" | "should_have" | "could_have"
  - `source`: "transcript"
- **Cost**: 1 LLM call

##### Step 1c: User Story Parsing (Python-only, no LLM call)

- **Input**: User stories text (formatted as "US-1: As a..., I want..., So that...")
- **Regex Pattern**: Parses structured user story format
- **Python Output**: 10-20 structured requirements extracted without LLM
- **Cost**: 0 LLM calls

##### Step 1d: Semantic Deduplication (Python-only)

- **Input**: Combined pool of 60-80 extracted + parsed requirements
- **Algorithm**: String similarity (difflib, threshold 85%)
- **Output**: De-duplicated pool (typically reduces to 50-65 unique requirements)
- **Cost**: 0 LLM calls

##### Step 1e: Glossary + Coverage Mapping (LLM call)

- **Input**: Deduplicated requirements pool
- **Prompt**: "Extract technical terms/glossary and map requirements to BRD sections"
- **LLM Output**:
  - Glossary: `{ "term": "definition", ... }`
  - Coverage map: `{ "Overview": 8 requirements, "Functional": 12, ... }`
- **Cost**: 1 LLM call

##### Step 1f: Conflict Detection (LLM call)

- **Input**: Deduplicated requirements pool
- **Prompt**: "Identify conflicting or contradictory requirements"
- **LLM Output**:
  - Conflict list: `[{ "req_id_1": "...", "req_id_2": "...", "reason": "..." }, ...]`
- **Purpose**: Surface ambiguities for human review
- **Cost**: 1 LLM call

**Total Extraction Cost**: 3-4 LLM calls

#### **Phase 2: Section Selection**

##### Step 2a: Rule-Based Section Suggestion

- **Input**: Coverage map from Step 1e
- **Rules**:
  - If 5+ non-functional requirements → suggest "Non-Functional Requirements" section
  - If 8+ functional requirements → suggest "Detailed Requirements" section
  - Always suggest: "Overview", "Business Objectives", "Assumptions & Constraints"
- **Output**: Suggested sections (8-15 options)
- **Cost**: 0 LLM calls (Python rules)

##### Step 2b: User Selection

- **Frontend**: Checkbox interface, user selects which sections to generate
- **Customization**: User can add custom section names
- **Storage**: Selected sections stored in project state

**Total Selection Cost**: 0 LLM calls

#### **Phase 3: Section Generation**

##### Step 3a: For Each Selected Section

- **LLM Prompt**:
  - System: "You are a senior requirements analyst"
  - User: "Generate the '[SectionName]' section using these requirements: [list]"
  - Context: Relevant requirements from pool, glossary, coverage map
- **LLM Output**: Markdown content (typically 300-600 words)
- **Cost**: 1 LLM call per section

##### Step 3b: Quality Scoring

- **Scorer**: Checks for:
  - Content length ≥ 300 words (minimum)
  - Presence of actual content (not placeholder text)
  - Structure (headings, lists, tables if applicable)
  - Relevance to section name
- **Output**: Quality score 0.0-1.0 (threshold: 0.6)

##### Step 3c: Word Count Enforcement

- **Rule**: If section exceeds max length, Python truncator:
  - Splits by paragraphs
  - Keeps top paragraphs within limit
  - Preserves markdown structure
- **Purpose**: Avoid massive sections that dominate document

##### Step 3d: Regeneration on Low Quality

- **Trigger**: Quality score < 0.6
- **Action**: Auto-regenerate section with improved prompt
- **Limit**: 1 automatic retry per section
- **Cost**: +1 LLM call (if triggered)

**Total Generation Cost**: 1 LLM call per section (+ 1 retry per low-quality section)
**Example**: 15 sections = 15 LLM calls (+ up to 15 retries if all low-quality = worst case 30 calls)

#### **Phase 4: Document Assembly (Node.js Backend)**

##### Step 4a: Serialize to JSON Payload

```json
{
  "metadata": {
    "project_name": "...",
    "client_name": "...",
    "industry": "...",
    "date": "2026-05-18",
    "version": 1
  },
  "sections": [
    { "name": "Overview", "content": "## Overview\n...", "quality_pct": "85%", "req_count": 8 },
    ...
  ]
}
```

##### Step 4b: Call Node.js Builder

- **Script**: `doc_builder/build_brd.js`
- **Framework**: `docx.js` (open-source Word document library)
- **Input**: JSON payload
- **Output**: `.docx` file with:
  - Cover page (project name, client, date)
  - Table of Contents (auto-generated from section names)
  - Running headers/footers (page numbers, client name)
  - Styled section headings (heading 1, 2, 3 styles)
  - Tables for requirements/glossary
  - Colored boxes for key callouts
- **Cost**: 0 LLM calls (deterministic)

##### Step 4c: Save & Return

- **Output Path**: `/outputs/BRD_{ProjectName}_v{Version}.docx`
- **HTTP Response**: File download link
- **User Action**: Download `.docx` for review/editing

**Total Document Cost**: 0 LLM calls

---

### Quality Issues & Failure Modes

#### **Quality Issue 1: Missing or Conflicting Requirements**

**Symptom**: Extracted requirements don't match what was discussed in meeting

**Root Cause**:

- Transcript is incomplete or garbled
- LLM extraction is too generic (misses specific details)
- Filler words/speaker labels interfere with transcript cleaning

**Mitigations**:

- Step 1e (Conflict Detection) surfaces contradictions for user review
- Frontend allows manual editing of extracted requirements
- Traceability matrix shows which requirements came from which section of transcript

#### **Quality Issue 2: Deduplicated Requirements Too Aggressive**

**Symptom**: Distinct requirements collapsed into one (over-deduplication)

**Root Cause**:

- String similarity threshold (85%) catches non-duplicates
- Example: "API must return JSON" vs "API must return XML" → both marked as duplicates

**Mitigations**:

- Threshold tuned empirically (85% balances precision/recall)
- User can manually "un-deduplicate" in frontend
- Glossary helps distinguish similar concepts

#### **Quality Issue 3: Generated Section is Generic**

**Symptom**: Section text uses placeholder language ("The system should support X"), not specific details

**Root Cause**:

- Sparse requirement pool (too few specific requirements extracted)
- LLM lacks context about customer's unique needs
- Section prompt not aligned with requirement details

**Mitigations**:

- Quality scorer checks for specificity
- Low-quality sections auto-regenerated with enhanced prompt
- User can manually edit sections before approval

#### **Quality Issue 4: Document Assembly Crashes**

**Symptom**: Word document fails to open or renders incorrectly

**Root Cause**:

- `docx.js` encounters unsupported markdown (complex tables, images)
- XML serialization error
- Node.js subprocess failure

**Mitigations**:

- Pipeline validates section content before passing to builder
- Complex markdown elements are escaped/simplified
- Error handling wraps Node.js call with try/except
- Fallback: if assembly fails, user can export requirements as JSON and build document manually

#### **Quality Issue 5: LLM Timeout on Large Extraction**

**Symptom**: Extraction takes >60 seconds, request times out

**Root Cause**:

- Transcript is 50,000+ characters
- Databricks endpoint overloaded
- Network latency

**Mitigations**:

- Extraction pipeline truncates transcript to max 8,000 characters
- Pipeline is async (doesn't block UI)
- User shown progress bar
- If timeout, user can retry or submit shorter transcript

#### **Quality Issue 6: Insufficient Section Coverage**

**Symptom**: Generated sections missing important content

**Root Cause**:

- Rule-based section suggester is too conservative
- User deselects sections that contain critical content
- Requirements pool is sparse

**Mitigations**:

- Coverage map shows how many requirements map to each suggested section
- Frontend highlights "must-have" sections (Business Objectives, Scope, Requirements)
- User can add custom sections to capture missing topics

#### **Quality Issue 7: Living BRD Version Conflict**

**Symptom**: Version 1 and Version 2 BRD conflict, unclear which is current

**Root Cause**:

- Multiple regenerations create version branches
- User edits both old and new versions independently

**Mitigations**:

- Each version stored with timestamp
- Change detection (`detect_changes()`) highlights differences between versions
- User chooses which changes to apply/merge
- Traceability shows which version each requirement came from

---

### Success/Failure Modes

#### **Success Mode 1: Well-Structured Input**

✅ **Trigger**:

- High-quality transcript (clear speakers, minimal background noise)
- Well-formatted user stories (standard "As a..., I want..., So that..." format)

✅ **Expected Output**:

- 50-80 high-quality extracted requirements
- Low conflict/deduplication rate
- All sections generated with quality score >80%
- Final BRD is professional, complete, ready to use

#### **Success Mode 2: Minimal Input (Transcript Only)**

✅ **Trigger**: User provides only transcript, no user stories

- **Extraction**: All requirements come from transcript LLM call
- **Coverage**: Less comprehensive, but sufficient for basic BRD
- **Quality**: Medium (user stories often provide priority/structured context that's missing)

#### **Success Mode 3: User Edits & Regenerates**

✅ **Trigger**: User reviews generated sections, identifies low-quality ones

- **Action**: Frontend "Regenerate Section" button
- **Process**: Section generation pipeline reruns for that section only
- **Quality**: Typically improves (user feedback narrows LLM focus)

#### **Failure Mode 1: No Input Provided**

❌ **Trigger**: User submits empty transcript and empty user stories

- **Result**: HTTP 400 Bad Request ("At least one input required")
- **Recovery**: User must provide content

#### **Failure Mode 2: Transcript Garbled/Incomplete**

⚠️ **Trigger**: Transcript is corrupted or missing key discussions

- **Result**: Extraction succeeds but produces incomplete requirements
- **Quality**: Low (sparse requirement pool)
- **Recovery**: User manually adds missing requirements via frontend form

#### **Failure Mode 3: All Sections Low-Quality**

⚠️ **Trigger**: Generated sections all score <60%

- **Result**: Pipeline auto-regenerates all sections
- **Total Time**: 2× generation time
- **Quality**: Often improves, but if not, document is still assembled with low-quality sections
- **User Warning**: "Some sections below quality threshold; please review & edit"

#### **Failure Mode 4: Node.js Build Script Fails**

❌ **Trigger**: `build_brd.js` not found or Node.js not installed

- **Result**: Subprocess fails with "command not found" or file error
- **Recovery**: Ensure Node.js and `doc_builder/` directory present

#### **Failure Mode 5: Conflicting Requirements Unresolved**

⚠️ **Trigger**: Step 1f (Conflict Detection) identifies conflicts, user doesn't resolve

- **Result**: Document is assembled with both conflicting requirements
- **Quality**: Reduced (document contains contradictions)
- **User Warning**: "Document contains [N] unresolved conflicts; review before sharing"

#### **Failure Mode 6: Concurrent Project Updates**

❌ **Trigger**: User has two browser tabs open, both editing same project

- **Result**: File store writes conflict
- **Recovery**: Last write wins (not ideal, but preserves data)
- **Mitigation**: Frontend should lock project during edits

---

## 3. TECHNICAL DOCUMENTATION AGENT (Port 5174)

### Purpose

Generates professional technical documentation (`.docx` / `.pdf`) from:

- GitHub repositories (cloned and analyzed)
- ZIP-uploaded codebases
- Extracted source code (Python, JavaScript, Java, Go, etc.)

**Output**: Comprehensive technical documentation covering:

- Architecture overview
- API/module reference
- Code structure
- Installation & setup
- Configuration
- Examples & usage
- Troubleshooting

**Key Problem Solved**: Eliminates manual technical documentation writing by extracting structure and context from actual source code, then generating documentation LLM-style.

---

### Main Components

| Component                | File                                    | Purpose                                               |
| ------------------------ | --------------------------------------- | ----------------------------------------------------- |
| **FastAPI App**          | `main.py`                               | Entry point, route aggregation, CORS middleware       |
| **Ingestion Routes**     | `api/routes/ingest.py`                  | GitHub clone, ZIP extraction, file filtering          |
| **Section Selection**    | `api/routes/sections.py`                | User selects documentation sections to generate       |
| **Context Building**     | `api/routes/context.py`                 | Retrieves relevant code snippets for section          |
| **Generation**           | `api/routes/generation.py`              | Per-section LLM generation with quality scoring       |
| **Assembly**             | `api/routes/assembly.py`                | Calls Node.js to build final `.docx` / `.pdf`         |
| **State Store**          | `core/state_store.py`                   | Persistent project state (JSON files)                 |
| **Tree-Sitter Analyzer** | `core/analysis/tree_sitter_analyzer.py` | Parses source code using tree-sitter library          |
| **Tech Stack Detector**  | `core/analysis/tech_stack_detector.py`  | Framework/library detection from source files         |
| **File Filtering**       | `core/ingestion/file_filter.py`         | Excludes non-source files (node_modules, .git, etc.)  |
| **Section Generator**    | `core/generation/section_generator.py`  | LLM + context → documentation section                 |
| **Quality Scorer**       | `core/generation/quality_scorer.py`     | Evaluates generated content quality                   |
| **Context Retriever**    | `core/generation/context_retriever.py`  | Fetches relevant code context for section             |
| **Metrics Collector**    | `core/metrics_collector.py`             | Tracks pipeline metrics (LLM calls, tokens, duration) |
| **Document Builder**     | `core/assembler/document_builder.py`    | Calls Node.js to assemble `.docx`                     |

---

### Input/Output Flow

```
┌──────────────────────────────────────────────────────────────────┐
│ FRONTEND: React UI (Port 5174)                                   │
│ [1a] Enter GitHub URL + token                                    │
│  OR [1b] Upload ZIP file                                         │
│ [2] Enter project metadata (name, description)                   │
│ [3] Review extracted sections & tech stack                       │
│ [4] Select sections to document                                  │
│ [5] Generate documentation (section by section)                  │
│ [6] Review & edit sections                                       │
│ [7] Assemble & download .docx / .pdf                             │
└────────────────────────┬─────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────────┐
        │                │                    │
        ▼                ▼                    ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│POST /github  │  │POST /zip     │  │GET /status   │
│  (clone)     │  │ (upload)     │  │              │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       │    ┌────────────▼─────────────┐   │
       │    │ Ingestion Pipeline       │   │
       │    │ ┌──────────────────────┐ │   │
       │    │ │1. Clone git repo     │ │   │
       │    │ │   OR extract ZIP     │ │   │
       │    │ ├──────────────────────┤ │   │
       │    │ │2. Filter files       │ │   │
       │    │ │   (exclude .git,     │ │   │
       │    │ │   node_modules, etc) │ │   │
       │    │ ├──────────────────────┤ │   │
       │    │ │3. Analyze codebase   │ │   │
       │    │ │   (tree-sitter)      │ │   │
       │    │ ├──────────────────────┤ │   │
       │    │ │4. Detect tech stack  │ │   │
       │    │ │   (frameworks,       │ │   │
       │    │ │   libraries, DBs)    │ │   │
       │    │ └──────────────────────┘ │   │
       │    └────────┬─────────────────┘   │
       │             │                     │
       └─────────────┼─────────────────────┘
                     │
         ┌───────────▼───────────┐
         │ Analysis Result        │
         │ - languages: {         │
         │   "Python": 60%,       │
         │   "JavaScript": 40%    │
         │ }                      │
         │ - primary_language     │
         │ - frameworks detected  │
         │ - total LOC            │
         │ - file structure       │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │ User selects sections  │
         │ (Overview, API Ref,    │
         │  Architecture, Setup)  │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────────────────┐
         │ Generation Pipeline (per-section)  │
         │ ┌──────────────────────────────┐  │
         │ │1. Build meta-prompt          │  │
         │ │   (topic, query, instruction)│  │
         │ ├──────────────────────────────┤  │
         │ │2. Retrieve context           │  │
         │ │   (relevant code snippets)   │  │
         │ ├──────────────────────────────┤  │
         │ │3. Call LLM                   │  │
         │ │   (generation_system_prompt) │  │
         │ ├──────────────────────────────┤  │
         │ │4. Score quality (>70%)       │  │
         │ ├──────────────────────────────┤  │
         │ │5. Auto-regenerate if low     │  │
         │ └──────────────────────────────┘  │
         └───────────┬───────────────────────┘
                     │
         ┌───────────▼───────────┐
         │ LLM (Databricks)       │
         │ Token tracking:        │
         │ - prompt tokens        │
         │ - completion tokens    │
         │ - cost estimation      │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────────┐
         │ Generated Sections         │
         │ [{                         │
         │   "name": "API Reference", │
         │   "content": "## API\n...",│
         │   "quality_score": 0.82,   │
         │   "word_count": 450        │
         │ }, ...]                    │
         └───────────┬───────────────┘
                     │
         ┌───────────▼───────────┐
         │ User reviews & edits   │
         │ (inline editor)        │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────────────┐
         │ Assembly Pipeline             │
         │ (Node.js backend)             │
         │ ┌──────────────────────────┐  │
         │ │1. Serialize sections     │  │
         │ │   to JSON                │  │
         │ │2. Call document builder  │  │
         │ │3. Apply styling          │  │
         │ │4. Generate PDF (if req)  │  │
         │ └──────────────────────────┘  │
         └───────────┬───────────────────┘
                     │
         ┌───────────▼───────────┐
         │ Output file:          │
         │ - techdoc.docx        │
         │ - techdoc.pdf         │
         └───────────┬───────────┘
                     │
         ┌───────────▼──────────────┐
         │ Metrics recorded:        │
         │ - ingestion duration     │
         │ - generation duration    │
         │ - LLM calls/tokens       │
         │ - quality scores         │
         │ - assembly duration      │
         └───────────┬──────────────┘
                     │
         ┌───────────▼───────────┐
         │ User downloads file    │
         └───────────────────────┘
```

### Main Processing Steps

#### **Phase 1: Ingestion & Analysis**

##### Step 1a: Repository Cloning (if GitHub URL provided)

- **Input**: GitHub URL, optional PAT token
- **Process**:
  - `git clone {url}` to `/storage/repos/{project_id}/`
  - Token used for private repo authentication
- **Output**: Full repo directory on disk
- **Cost**: 0 LLM calls
- **Metrics**:
  - Clone duration
  - Total files found
  - Repo size (bytes)

##### Step 1b: ZIP Extraction (if file uploaded)

- **Input**: `project.zip`
- **Process**: Extract to `/storage/repos/{project_id}/`
- **Output**: Directory tree
- **Cost**: 0 LLM calls

##### Step 1c: File Filtering

- **Process**: Recursively walk directory, filter by:
  - **Include**: Source files (`.py`, `.js`, `.ts`, `.java`, etc.)
  - **Exclude**:
    - Directories: `.git`, `.venv`, `node_modules`, `dist`, `build`, `__pycache__`, `.pytest_cache`, `venv`, `.env`, `.vscode`, `.idea`
    - Files: `.png`, `.jpg`, `.gif`, `.zip`, `.tar`, `.exe`, `.bin`, `.db`
- **Output**: Filtered file list (typically 20-40% of original files)
- **Metrics**: Total files found vs. files after filter

##### Step 1d: Code Analysis (Tree-Sitter)

- **Library**: `tree-sitter` (language-agnostic parser)
- **Process**: Parse each source file, extract:
  - Functions/methods (name, signature, docstring)
  - Classes (name, methods, inheritance)
  - Imports/dependencies
  - Top-level comments/docstrings
  - File structure
- **Output**: AnalysisResult object:
  ```json
  {
    "languages": {
      "Python": 45,
      "JavaScript": 30,
      "TypeScript": 20,
      "HTML": 5
    },
    "total_loc": 15000,
    "primary_language": "Python",
    "frameworks": ["FastAPI", "React", "PostgreSQL"],
    "modules": [
      {
        "name": "api.routes.users",
        "functions": ["get_user()", "create_user()", ...],
        "classes": ["UserSchema", ...]
      },
      ...
    ]
  }
  ```
- **Cost**: 0 LLM calls (tree-sitter is local parsing)
- **Metrics**: LOC, language breakdown, parsing duration

##### Step 1e: Tech Stack Detection

- **Framework Signatures**: Content-based matching
  - Python: FastAPI, Django, Flask, Tornado, etc.
  - JavaScript: React, Vue, Angular, Express, etc.
  - Databases: PostgreSQL, MongoDB, Redis, etc.
  - Other: Docker, Kubernetes, Terraform, etc.
- **Output**: Detected frameworks list
- **Cost**: 0 LLM calls (regex/keyword matching)

**Total Ingestion Cost**: 0 LLM calls (deterministic pipeline)

#### **Phase 2: Section Selection**

##### Step 2a: Generate Available Sections

- **Sections determined by**:
  - Primary language detected
  - Frameworks identified
  - Project structure analysis
- **Standard Sections**:
  - Overview / Architecture
  - Installation & Setup
  - Project Structure
  - API Reference (if REST API detected)
  - Module / Class Reference
  - Configuration
  - Examples & Usage
  - Deployment
  - Troubleshooting
- **Output**: ~8-10 suggested sections

##### Step 2b: User Selection

- **Frontend**: Checkboxes, user selects subset
- **Default**: All sections selected
- **Custom**: User can add custom section titles
- **Storage**: Selections saved in project state

**Total Selection Cost**: 0 LLM calls

#### **Phase 3: Context Building & Generation**

##### Step 3a: For Each Selected Section

- **Meta-Prompt Builder**: Constructs section-specific query
  - Section name: "API Reference"
  - Query: "What APIs, routes, and endpoints does this project expose?"
  - Instruction: "Document each endpoint with method, path, parameters, response..."

##### Step 3b: Context Retrieval

- **Process**: Query analysis result:
  - Search for relevant functions/classes/modules matching section topic
  - Extract source code snippets
  - Limit to ~2,000 tokens of context (to stay within LLM budget)
- **Output**: Relevant code context as markdown-formatted code blocks
- **Cost**: 0 LLM calls (local retrieval)

##### Step 3c: LLM Generation

- **System Prompt**:
  ```
  You are a senior technical writer producing professional software documentation.
  Write ONLY the content for the requested section.
  Base everything on the provided code context.
  Do NOT invent details.
  Minimum 300 words.
  ```
- **User Message**:

  ```
  Section: [section_name]
  Instruction: [meta-prompt instruction]

  Relevant Code:
  [code context]
  ```

- **LLM Call**: Invoke Databricks Claude endpoint
- **Output**: Markdown content (typically 300-800 words)
- **Cost**: 1 LLM call per section
- **Metrics**: Prompt tokens, completion tokens, duration

##### Step 3d: Quality Scoring

- **Scorer**: Evaluates:
  - Content length ≥ 300 words
  - Presence of code examples/snippets
  - Section-specific quality (e.g., API section must list endpoints)
  - Markdown structure validity
  - Absence of placeholder text
- **Output**: Quality score 0.0-1.0 (threshold: 0.70)

##### Step 3e: Auto-Regeneration on Low Quality

- **Trigger**: Quality score < 0.70
- **Action**: Regenerate with improved instruction:
  ```
  Previous attempt scored poorly. Ensure you:
  - Use markdown headers and code blocks
  - Include specific code references and examples
  - Write at least 300 words
  - Cover the topic thoroughly
  ```
- **Limit**: 1 automatic retry per section
- **Cost**: +1 LLM call (if triggered)

**Total Generation Cost**: 1 LLM call per section (+ 1 retry if low-quality)
**Example**: 8 sections = 8-16 LLM calls (depending on regeneration rate)

#### **Phase 4: Assembly & Output**

##### Step 4a: Review & Edit

- **Frontend**: Inline editor for each section
- **User can**: Edit, delete, add sections before final assembly
- **Changes**: Not reflected in state store (draft mode)

##### Step 4b: Final Assembly

- **Serialize**: All reviewed sections to JSON
- **Call Node.js Builder**: `document_builder.js`
- **Styling Applied**:
  - Cover page (project name, language breakdown, date)
  - Table of Contents (auto-generated)
  - Styled headings (Heading 1, 2, 3)
  - Code blocks with syntax highlighting
  - Tables for API endpoints, configuration options
  - Running headers/footers (page numbers, doc version)
- **Output Format**:
  - DOCX (default, Word-compatible)
  - PDF (if requested, requires additional rendering)

##### Step 4c: Metrics Persistence

- **Record**:
  - Total generation time
  - Per-section scores & word counts
  - LLM retries per section
  - Total tokens used
  - File size of output document
  - Page estimate (for user expectation)
- **Purpose**: Understand quality, cost, and optimization opportunities

**Total Assembly Cost**: 0 LLM calls (deterministic)

---

### Quality Issues & Failure Modes

#### **Quality Issue 1: Sparse Codebase or Poor Structure**

**Symptom**: Generated documentation is generic, lacks specific details

**Root Cause**:

- Codebase has minimal docstrings
- Functions/classes lack type hints
- README or API documentation missing from source
- Tree-sitter parser struggles with non-standard code structure

**Mitigations**:

- Context retriever attempts to extract comments/docstrings
- If none found, falls back to function signatures
- Quality scorer detects sparse content and triggers regeneration
- User can supplement with manual edits

#### **Quality Issue 2: GitHub API Rate Limit**

**Symptom**: "GitHub API rate limit exceeded" error after 60 requests

**Root Cause**:

- GitHub clone uses HTTPS (not SSH via token) for authentication
- Token not provided or already exhausted
- Multiple users cloning large repos simultaneously

**Mitigations**:

- User can provide GitHub PAT token for higher rate limits
- Clone process checks for token before attempting
- Error message explains how to generate token
- Fallback: User uploads ZIP instead of GitHub URL

#### **Quality Issue 3: Timeout on Large Codebase**

**Symptom**: Analysis hangs or exceeds 60-second timeout

**Root Cause**:

- Codebase > 100,000 LOC takes tree-sitter >30 seconds to parse
- Ingestion phase not parallelized
- Large number of files in analysis

**Mitigations**:

- File filtering is aggressive (excludes node_modules, dist, etc.)
- Tree-sitter parsing limited to top N files (per language)
- Async/await pattern allows cancellation
- User can upload subset of codebase or simplify

#### **Quality Issue 4: Incorrect Tech Stack Detection**

**Symptom**: "Frontend: React" detected but project uses Vue

**Root Cause**:

- Framework detection relies on keyword matching
- Codebase may have unused dependencies (old package.json)
- File signatures ambiguous between frameworks

**Mitigations**:

- Detection is conservative (only flags frameworks with strong confidence)
- Frontend displays detected frameworks for user confirmation
- User can manually edit detected tech stack
- Not critical — wrong tech stack doesn't break documentation (just metadata)

#### **Quality Issue 5: LLM Hallucinates Non-Existent APIs**

**Symptom**: Documentation lists endpoints that don't actually exist in code

**Root Cause**:

- LLM trained on common patterns, generates plausible-sounding APIs
- Context retrieval didn't capture actual endpoints
- LLM "fills in" missing details

**Mitigations**:

- System prompt: "Do NOT invent details. Base everything on provided code context."
- Quality scorer checks for specificity (generic endpoints fail scoring)
- User reviews documentation and edits/deletes non-existent content
- Future: Semantic validation against actual codebase

#### **Quality Issue 6: Section Quality Score Too Low**

**Symptom**: All sections regenerated, still don't meet 70% threshold

**Root Cause**:

- Very sparse codebase (few functions, no docstrings)
- LLM quality scorer is too strict
- Mismatch between section topic and available code

**Mitigations**:

- Quality scorer tuned empirically (70% threshold balances coverage/quality)
- Threshold can be lowered by admin if false positives
- User can manually edit section to improve quality
- Fallback: Document still assembled with low-quality sections + warning

#### **Quality Issue 7: Node.js Assembly Fails**

**Symptom**: Final assembly crashes, no `.docx` output

**Root Cause**:

- `document_builder.js` not found
- Node.js subprocess error (out of memory, invalid JSON, etc.)
- Generated content contains unsupported markdown (complex tables, images)

**Mitigations**:

- Content validation before assembly (check for markdown compatibility)
- Error handling wraps assembly with try/except
- User can export sections as JSON and manually build document
- Logs capture error details for debugging

---

### Success/Failure Modes

#### **Success Mode 1: Well-Documented GitHub Repo**

✅ **Trigger**:

- Repo has good README, docstrings, type hints
- Code is well-structured (clear module organization)
- Established framework (Flask, React, etc.)

✅ **Expected Output**:

- Ingestion: 5-10 seconds
- Analysis extracts 50+ functions/classes with docstrings
- Generation: 8 sections in 1-2 minutes
- Quality scores: 80-95% (minimal regeneration)
- Final documentation: Professional, comprehensive

#### **Success Mode 2: Private GitHub Repo**

✅ **Trigger**: User provides GitHub PAT token

- **Cloning**: Works normally (PAT allows private repo access)
- **Rest of flow**: Same as public repo

#### **Success Mode 3: ZIP-Uploaded Codebase**

✅ **Trigger**: User uploads `myproject.zip` (500 MB, 50k LOC)

- **Extraction**: Immediate (no GitHub rate limits)
- **Analysis**: Tree-sitter parses local files
- **Rest of flow**: Same as GitHub repo

#### **Success Mode 4: Small/Minimal Codebase**

⚠️ **Trigger**: Single-file Flask app or Node.js script

- **Ingestion**: Seconds
- **Analysis**: Extracts 2-3 functions
- **Generation**: Sections are brief but valid (300-400 words each)
- **Quality**: Medium (limited content, but accurate)
- **User Action**: Manually expand sections or accept lean documentation

#### **Failure Mode 1: Empty Repository**

❌ **Trigger**: User clones empty GitHub repo or uploads empty ZIP

- **Result**: "No source files found" error
- **HTTP 400 Bad Request**
- **Recovery**: User must provide repo with source code

#### **Failure Mode 2: GitHub Clone Fails**

❌ **Trigger**: Invalid GitHub URL or network error

- **Result**: `git clone` command fails
- **HTTP 500 Internal Server Error**
- **Message**: "Clone failed: [git error detail]"
- **Recovery**: User checks URL, retries, or uploads ZIP

#### **Failure Mode 3: Unsupported Language**

⚠️ **Trigger**: Codebase in language without tree-sitter grammar (e.g., niche language)

- **Result**: Analysis succeeds but extracts minimal structure
- **Quality**: Low (no parsed functions/classes)
- **Documentation**: Generic, user must supplement manually

#### **Failure Mode 4: Generation Timeout**

❌ **Trigger**: All sections timeout during generation (network issues, overloaded LLM)

- **Result**: After 30 sec timeout, HTTP 504 Gateway Timeout
- **Recovery**: User retries, or generates subset of sections

#### **Failure Mode 5: Concurrent Generation Limit**

⚠️ **Trigger**: Multiple users generating documentation simultaneously

- **Result**: Databricks endpoint is rate-limited
- **Symptom**: Slow generation, some sections timeout
- **Recovery**: Auto-retry with exponential backoff

#### **Failure Mode 6: Output Document Too Large**

⚠️ **Trigger**: 20+ sections × 500 words each = 10,000+ word document

- **Result**: `.docx` assembly is slow (10-30 seconds)
- **Recovery**: Document still generated successfully, just slow
- **Mitigation**: Large documents split into multiple files (by user request)

---

## Cross-Project Issues & Synergies

### Data Flow Between Agents

```
┌──────────────────┐
│ BRD Agent        │
│ (Port 3000)      │
│ Input: Transcript│
│ Output: BRD.docx │
└────────┬─────────┘
         │
         │ Download BRD
         ▼
┌──────────────────────┐
│ AI Solution Architect│
│ (Port 5175)          │
│ Input: BRD text      │
│ Output: PPTX slides  │
└──────────┬───────────┘
           │
           │ (BRD + Tech Doc)
           ▼
    ┌──────────────┐
    │ PowerPoint   │
    │ slides with  │
    │ architecture │
    └──────────────┘

Parallel Flow:
┌──────────────────┐
│ Tech Doc Agent   │
│ (Port 5174)      │
│ Input: GitHub URL│
│ Output: TechDoc.docx
└──────────────────┘
     │
     │ (Tech doc text)
     ▼
  ┌──────────────────┐
  │ AI Solution      │
  │ Architect        │
  │ Input: Tech Doc  │
  │ Output: PPTX     │
  └──────────────────┘
```

### Quality Metrics Tracking

Each agent tracks:

- **Ingestion Metrics**: Files processed, languages detected, size
- **Generation Metrics**: LLM calls, tokens used, quality scores, regeneration rate
- **Assembly Metrics**: Output size, page count, assembly duration
- **Success/Failure**: Error types, retry counts, resolution status

**Collective Metrics**:

- Total documentation generated per month
- Average generation time (end-to-end)
- LLM cost per document
- Quality score distribution
- User satisfaction (review ratings, feedback)

---

## Summary Table

| Aspect             | BRD Agent                       | Tech Doc Agent                 | AI Architect                              |
| ------------------ | ------------------------------- | ------------------------------ | ----------------------------------------- |
| **Input**          | Transcript + user stories       | GitHub/ZIP codebase            | BRD + tech doc                            |
| **Output**         | `.docx` BRD                     | `.docx` technical doc          | `.pptx` presentation                      |
| **Main Steps**     | Extract → Generate → Assemble   | Analyze → Generate → Assemble  | Summarize → Generate → Build PPTX         |
| **LLM Calls**      | 4-6 per project                 | 8-16 per project               | 3 per project                             |
| **Quality Issues** | Missing requirements, conflicts | Generic content, hallucination | Diagram corruption, incomplete components |
| **Time**           | 2-5 min                         | 2-5 min                        | 15-20 sec                                 |
| **Success Rate**   | 85-95%                          | 80-90%                         | 95%+                                      |

---

## Recommendations

### For Immediate Improvement

1. **BRD Agent**:
   - Add manual conflict resolution UI (don't auto-skip conflicts)
   - Implement concurrent project locking (prevent multi-tab edits)
   - Add "regenerate all sections" button with batch LLM call

2. **Tech Doc Agent**:
   - Add semantic validation (check generated APIs against actual code)
   - Parallelize tree-sitter parsing for faster ingestion
   - Support image embedding in generated docs

3. **AI Architect**:
   - Monitor PowerPoint corruption issues (ongoing testing)
   - Add custom diagram styling (colors, fonts)
   - Support multi-page PPTX exports with diagram per slide

### For Long-Term Roadmap

1. **Multi-Agent Orchestration**:
   - Allow pipeline: Transcript → BRD → Architecture → PPTX
   - Shared project context across all three agents
   - Single download: All three documents (BRD, tech doc, PPTX)

2. **Quality Assurance**:
   - A/B testing for LLM prompts
   - Human review loops for critical sections
   - Version control for generated documents

3. **Cost Optimization**:
   - Cache LLM responses for common section types
   - Batch LLM calls within projects
   - Support local LLM fallback (Ollama, LLaMA)
