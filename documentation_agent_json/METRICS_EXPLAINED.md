# 📊 Documentation Agent — Metrics Explained

> A plain-English guide to every field in the JSON metrics files produced by the **BRD Agent**, **PPT Agent (AI Solution Architect)**, and **Technical Document Agent**.

---

## 🗂️ Where the Files Live

```
documentation_agent_json/
├── brd-agent/          ← Business Requirements Document metrics
├── ppt-agent/          ← PowerPoint / Architecture Presentation metrics
└── technical-agent/    ← Technical Documentation metrics
```

Each JSON file is one **run** — one time you asked the agent to generate a document. Think of it like a receipt that records everything that happened during that run.

---

## 🔵 PART 1 — BRD Agent Metrics

> **What is the BRD Agent?**  
> It reads stakeholder inputs (e.g., transcripts, notes, requirement sheets), extracts requirements, resolves conflicts between them, and writes a Business Requirements Document (`.docx` file).

---

### 🔑 Identity Fields

| Field | What it means | Example |
|-------|--------------|---------|
| `run_id` | A unique ID for this specific run (like a ticket number) | `"15dbec4c-7483-422b-ae4d-6ef5d1d7a826"` |
| `project_id` | The ID of the project this BRD belongs to | `"d052293a-6c16-4da7-823f-cb18380c5eba"` |
| `project_name` | The human-readable name of the project | `"Education4All"` |
| `recorded_at` | The exact date and time this metric file was saved | `"2026-06-09T14:55:53"` |

---

### ✅ `run_outcome` — Did It Work?

This tells you at a glance whether the run succeeded or failed.

| Field | What it means | Example |
|-------|--------------|---------|
| `success` | `true` = everything went fine, `false` = something crashed | `true` |
| `error_stage` | Which step failed: `ingestion`, `extraction`, `generation`, or `assembly` | `null` (no error) |
| `error_category` | Type of error: `api_error`, `parsing_error`, `timeout`, etc. | `null` |
| `error_message` | The actual error text (first 500 characters) | `null` |

**🧠 Simple Example:**  
Imagine you asked a friend to write a report. If they finished it → `success: true`. If their computer crashed while writing → `success: false`, `error_stage: "generation"`.

---

### ⏱️ `timing` — How Long Did Each Step Take?

The BRD pipeline has three main phases. This block times each one.

| Field | What it means | Example |
|-------|--------------|---------|
| `run_started_at` | When the run began | `"2026-06-09T14:51:28"` |
| `run_ended_at` | When the run finished | `"2026-06-09T14:55:53"` |
| `total_duration_seconds` | Total wall-clock time (seconds) | `264.98` (~4.4 minutes) |
| `extraction_duration_seconds` | Time spent reading inputs and pulling out requirements | `138.16` (~2.3 min) |
| `generation_duration_seconds` | Time spent writing each BRD section using AI | `60.32` (~1 min) |
| `document_duration_seconds` | Time to assemble the final `.docx` file | `0.53` (half a second) |

**🧠 Simple Example:**  
Think of baking a cake. `extraction` = gathering and measuring ingredients, `generation` = baking, `document` = boxing it up. The total is the whole process.

---

### 🤖 `llm_usage` — AI Token Consumption

Every time the AI model is called, it processes text in units called **tokens** (roughly ¾ of a word each). This block tracks all token usage.

| Field | What it means | Example |
|-------|--------------|---------|
| `total_calls` | How many times the AI was called in total | `7` |
| `prompt_tokens` | Tokens sent **to** the AI (your instructions + context) | `12,049` |
| `completion_tokens` | Tokens the AI **generated** (its response) | `14,969` |
| `total_tokens` | Sum of prompt + completion | `27,018` |

**`by_stage`** breaks this down into three sub-stages:

| Stage | What happened here |
|-------|-------------------|
| `extraction` | AI read stakeholder documents and pulled out individual requirements |
| `conflicts` | AI checked for contradictions between requirements |
| `generation` | AI wrote the actual BRD sections (Executive Summary, Risks, etc.) |

**🧠 Simple Example:**  
If you hire a consultant to write a report, `prompt_tokens` = how many pages of notes *you* gave them, `completion_tokens` = how many pages of report *they* wrote back.

---

### 💰 `cost` — What Did It Cost?

| Field | What it means | Example |
|-------|--------------|---------|
| `model_name` | Which AI model was used | `"databricks-claude-sonnet-4-6"` |
| `prompt_cost_usd` | Cost of the input tokens (in US dollars) | `$0.036147` |
| `completion_cost_usd` | Cost of the output tokens | `$0.224535` |
| `total_cost_usd` | Total cost for this run | `$0.260682` (~26 cents) |
| `currency` | Currency used | `"USD"` |

**🧠 Simple Example:**  
Like a phone call — you pay for both listening (prompt) and speaking (completion). Completion is typically 3× more expensive.

---

### 📑 `sections` — Document Section Tracking

The BRD is divided into sections (e.g., Executive Summary, Risks, Stakeholder Register). This tracks how those sections were generated.

| Field | What it means | Example |
|-------|--------------|---------|
| `attempted` | How many sections the agent tried to generate | `3` |
| `succeeded` | How many were generated successfully | `3` |
| `failed` | How many failed | `0` |
| `success_rate_pct` | Percentage that succeeded (100% = all good) | `100.0` |

**`review_cycles`** — Was any section regenerated because the reviewer didn't like it?

| Field | What it means | Example |
|-------|--------------|---------|
| `total_regenerations` | Total number of times a section was re-made | `0` |
| `sections_with_rework` | List of section names that needed rework | `[]` (none) |
| `per_section` | Per-section breakdown with name and cycle count | See below |

**`per_section` example:**
```json
"0dab5dcb-...": {
  "name": "Executive Summary",
  "cycles": 0     ← generated once, no rework needed
}
```

---

### 🏆 `quality` — How Good Is the Output?

This is the most important block for your presentation — it measures the *quality* of the BRD content.

#### `requirement_quality` — SMART Score

The BRD Agent grades each extracted requirement against the **SMART** framework (a standard used in project management):

| SMART Letter | What it checks | Example requirement that passes |
|-------------|---------------|--------------------------------|
| **S**pecific | Is the requirement clearly defined? | "Users must be able to reset passwords via email OTP" ✅ vs. "Make login better" ❌ |
| **M**easurable | Can you measure success? | "Page load time < 2 seconds" ✅ vs. "Make it fast" ❌ |
| **A**chievable | Is it technically realistic? | "Support 10,000 concurrent users" ✅ vs. "Support infinite users" ❌ |
| **R**elevant | Does it align with project goals? | "Add checkout flow" (for an e-commerce site) ✅ |
| **T**ime-bound | Does it have a deadline? | "Deliver MVP by Q3 2026" ✅ vs. "Deliver soon" ❌ |

| Field | What it means | Example |
|-------|--------------|---------|
| `total_evaluated` | Total number of requirements graded | `74` |
| `avg_score` | Average SMART score across all requirements (0–1 scale) | `0.668` (66.8%) |
| `specific_pct` | % of requirements that are Specific | `87.8%` |
| `measurable_pct` | % of requirements that are Measurable | `9.5%` (low — common!) |
| `achievable_pct` | % of requirements that are Achievable | `100%` |
| `relevant_pct` | % of requirements that are Relevant | `100%` |
| `time_bound_pct` | % of requirements with a time constraint | `31.1%` |
| `high_quality_count` | Requirements scoring high on SMART | `24` |
| `medium_quality_count` | Requirements scoring medium | `41` |
| `low_quality_count` | Requirements scoring low | `9` |

**🧠 Simple Example:**  
For the Education4All project: 74 requirements were analyzed. Almost all are specific and relevant, but only 9.5% are measurable — meaning most requirements lack KPIs like "must achieve 95% uptime." This is a common finding and something to improve.

---

#### `section_completeness` — Did Each Section Have All Expected Content?

Each BRD section type has a checklist of expected items (e.g., an Executive Summary should have: problem statement, objectives, scope, stakeholders, timeline).

| Field | What it means | Example |
|-------|--------------|---------|
| `overall_pct` | What % of all required items were present across all sections | `93.3%` |
| `by_section` | Per-section breakdown | See below |

**Per-section example:**
```json
"Executive Summary": {
  "required_items": 5,    ← 5 items expected
  "present_items": 4,     ← 4 were found
  "completeness_pct": 80.0  ← 80% complete
}
```

**🧠 Simple Example:**  
Like a marking rubric. If a section was supposed to have 5 components but only has 4, it scores 80%.

---

### ⚔️ `conflicts` — Requirement Conflicts

When stakeholders provide input, they often contradict each other. The BRD Agent finds and resolves these.

| Field | What it means | Example |
|-------|--------------|---------|
| `detected_count` | Total conflicts found | `6` |
| `resolved_count` | Conflicts that were resolved | `6` |
| `unresolved_count` | Conflicts still open | `0` |
| `high_impact_count` | Conflicts that could seriously derail the project | `3` |
| `medium_impact_count` | Moderate conflicts | `2` |
| `low_impact_count` | Minor conflicts | `1` |
| `resolution_rate_pct` | % of conflicts resolved (100% = all cleared) | `100.0%` |
| `accuracy_feedback` | Reviewer label: `valid`, `false_positive`, or `mixed` | `null` (not reviewed yet) |

**🧠 Simple Example:**  
Stakeholder A says "The system must support offline mode." Stakeholder B says "All data must sync in real-time." These are conflicting — one wants offline, the other wants always-connected. The agent detects this as a **high-impact** conflict and suggests a resolution.

---

### 📄 `output` — The Final File

| Field | What it means | Example |
|-------|--------------|---------|
| `file_generated` | Was the `.docx` file actually created? | `true` |
| `filename` | The name of the output file | `"BRD_Education4All_v1.docx"` |
| `file_size_bytes` | File size in bytes | `36,797` (~36 KB) |
| `output_path` | Full path where the file was saved | `"...outputs/BRD_Education4All_v1.docx"` |
| `sections_included` | How many sections are in the final document | `3` |
| `word_count_estimate` | Estimated total words in the document | `1,505` |

---

### 🚦 `acceptance` — Human Review Status

After the BRD is generated, a human reviewer can label it.

| Field | What it means | Example |
|-------|--------------|---------|
| `status` | One of: `pending`, `accepted_as_is`, `minor_edits`, `major_rework` | `"pending"` |
| `reviewer` | Who reviewed it | `null` (not reviewed yet) |
| `reviewed_at` | When they reviewed it | `null` |
| `notes` | Any notes left by the reviewer | `null` |

---
---

## 🟣 PART 2 — PPT Agent Metrics (AI Solution Architect)

> **What is the PPT Agent?**  
> It takes the BRD and generates a PowerPoint presentation of the recommended software architecture, including system diagrams, justifications, and slide content.

---

### 🔑 Identity Fields

| Field | What it means | Example |
|-------|--------------|---------|
| `run_id` | Unique run identifier | `"2310be1e-9aab-4521-958d-c86e2cc8102d"` |
| `timestamp_start` | When the run started | `"2026-06-01T07:47:03"` |
| `timestamp_end` | When the run ended | `"2026-06-01T07:48:17"` |
| `run_success` | Did the run complete successfully? | `true` |

---

### ❌ `error_details` — Error Information

| Field | What it means | Example |
|-------|--------------|---------|
| `occurred` | Did any error happen? | `false` |
| `stage` | Which stage errored | `"unknown"` |
| `category` | Type of error | `"unknown_error"` |
| `message` | Error description | `""` (empty = no error) |
| `recovery_attempted` | Did the system try to recover? | `false` |
| `recovery_successful` | Did recovery work? | `false` |

---

### ⏱️ `duration` — Time Breakdown Per Phase

The PPT Agent has more pipeline steps than the BRD agent.

| Field | What it means | Example |
|-------|--------------|---------|
| `total_seconds` | Total time for the whole run | `73.78` (~1.2 min) |
| `summarization_seconds` | Time spent summarizing the BRD input | `0.0` (skipped if not needed) |
| `core_generation_seconds` | Time for AI to generate slide content | `63.95` (most of the time) |
| `diagram_generation_seconds` | Time for AI to generate diagram JSON | `0.0` |
| `diagram_rendering_seconds` | Time to convert diagram JSON into an image | `0.0` |
| `pptx_generation_seconds` | Time to build the `.pptx` file | `9.69` |
| `pptx_assembly_seconds` | Time to assemble slides into the deck | `0.0` |
| `validation_seconds` | Time to validate the output file | `0.0` |

**🧠 Simple Example:**  
`core_generation` is the "thinking" time (AI writing the content), while `pptx_generation` is the "printing" time (turning that content into a real PowerPoint file).

---

### 🤖 `llm_tokens` — Token Usage by Phase

| Phase | What the AI did |
|-------|----------------|
| `summarization` | Summarized the BRD (if the BRD was too long) |
| `core_generation` | Wrote the content for each slide |
| `diagram_generation` | Designed the architecture diagram structure |
| `total` | Combined totals |

Each phase has: `prompt_tokens`, `completion_tokens`, `total_tokens`.

**🧠 Simple Example (from real data):**  
For a run that generated 5 slides:
- Core generation: 1,784 prompt tokens + 3,643 completion tokens = 5,427 total
- Diagram: 1,978 prompt + 462 completion = 2,440 total
- Grand total: 7,867 tokens ≈ ~$0.07286 (about 7.3 cents)

---

### 💰 `estimated_cost_usd`

A single number — the total estimated cost of this run in USD.  
Example: `0.07286` = 7.3 cents per presentation run.

---

### 📑 `sections` — Slide Sections Chosen

The user can choose which sections/themes to include in the presentation.

| Field | What it means | Example |
|-------|--------------|---------|
| `selected_count` | How many section types were chosen | `4` |
| `selected_list` | The actual section names chosen | `["Title", "Closing", "Solution", "Diagram"]` |
| `custom_sections_count` | How many user-defined custom sections were added | `0` |
| `custom_sections` | List of custom section names | `[]` |
| `total_sections` | Total sections in the final presentation | `4` |

---

### 🎯 `slides` — Slide Generation Success

| Field | What it means | Example |
|-------|--------------|---------|
| `attempted` | How many slides the agent tried to create | `5` |
| `successful` | How many slides were created successfully | `5` |
| `failed` | How many slides failed | `0` |
| `retry_count` | How many times a slide had to be retried | `0` |
| `success_rate` | 1.0 = 100% success | `1.0` |

---

### 🏗️ `diagram` — Architecture Diagram Quality

This is one of the most unique features of the PPT Agent — it generates a system architecture diagram.

| Field | What it means | Example |
|-------|--------------|---------|
| `attempted` | Was a diagram attempted? | `true` |
| `success` | Was the diagram successfully created? | `true` |
| `components_count` | How many system components are in the diagram | `8` |
| `connections_count` | How many arrows/connections between components | `8` |
| `expected_components` | How many components were expected | `8` |
| `expected_connections` | How many connections were expected | `8` |
| `component_coverage` | % of expected components that appear (1.0 = 100%) | `1.0` |
| `connection_coverage` | % of expected connections that appear | `1.0` |
| `correctness_score` | Overall diagram accuracy score (0–1) | `1.0` |

**🧠 Simple Example (imperfect run from real data):**
```json
"components_count": 3,       ← only 3 found
"expected_components": 8,    ← 8 were expected
"component_coverage": 0.375  ← only 37.5% coverage!
"correctness_score": 0.625   ← diagram was 62.5% correct
```
This means the AI designed a diagram that was missing 5 out of 8 expected architecture boxes.

---

### 🌟 `quality` — Overall Presentation Quality

| Field | What it means | Score Range | Example |
|-------|--------------|------------|---------|
| `content_quality` | How good is the text content on slides? | 0–1 | `1.0` (perfect) |
| `diagram_quality` | How accurate and well-structured is the diagram? | 0–1 | `0.92` |
| `architecture_alignment` | Does the architecture match the BRD requirements? | 0–1 | `1.0` |
| `output_validity` | Is the final `.pptx` file valid and openable? | 0–1 | `1.0` |
| `overall_score` | Weighted average of all quality dimensions | 0–1 | `0.98` |

**🧠 Simple Example:**  
A score of `0.98` means the presentation was 98% quality — content was perfect, alignment was perfect, but the diagram was slightly imperfect (0.92), pulling the overall score down slightly.

---

### 📋 `pptx_validation` — File Health Check

After the file is created, the agent runs a health check on the actual `.pptx` file to make sure PowerPoint can open it without errors.

| Field | What it means | Example |
|-------|--------------|---------|
| `file_created` | Was the `.pptx` file actually saved to disk? | `true` |
| `file_size_bytes` | File size in bytes | `7,213,970` (~7 MB — includes images) |
| `valid_xml` | Is the internal XML structure valid? | `true` |
| `valid_relationships` | Are all internal file links/relationships correct? | `true` |
| `opens_without_repair` | Will PowerPoint open it without showing a repair dialog? | `true` |
| `all_slides_present` | Are all expected slides in the file? | `true` |
| `all_media_present` | Are all images/diagrams embedded properly? | `true` |
| `health_score` | Overall file health (1.0 = perfectly healthy) | `1.0` |

**🧠 A broken file example (from real data):**
```json
"all_slides_present": false,   ← a slide was missing!
"health_score": 0.833          ← 83.3% health (one check failed)
```

---

### 🏛️ `architecture_justification` — Are Design Decisions Backed Up?

Every architecture decision (e.g., "We chose microservices over monolith") should be justified with references to the BRD.

| Field | What it means | Example |
|-------|--------------|---------|
| `decisions_identified` | How many architecture decisions were detected in the slides | `6` |
| `decisions_justified` | How many of those decisions have a justification | `6` |
| `brd_citations` | How many times the BRD was explicitly cited as a source | `5` |
| `constraint_references` | How many times technical constraints were referenced | `5` |
| `justification_score` | 1.0 = every decision is justified | `1.0` |

**🧠 Simple Example:**  
"We chose PostgreSQL because the BRD requires ACID-compliant transactions (Section 3.2)." This would count as 1 justified decision + 1 BRD citation.

---

### 🔄 Other Fields

| Field | What it means | Example |
|-------|--------------|---------|
| `review_cycle_count` | How many times the presentation was reviewed and re-generated | `0` |
| `acceptance_status` | Current status: `pending_review`, `accepted`, `rejected` | `"pending_review"` |
| `total_retry_count` | Total number of retries for any step | `0` |

---
---

## 🟢 PART 3 — Technical Document Agent Metrics

> **What is the Technical Document Agent?**  
> It reads source code (Python, JavaScript, etc.) from a ZIP archive, understands the codebase, and writes a Technical Design Document (TDD) with sections like "Executive Summary", "AI/ML Pipeline", "Environment Setup", etc.

---

### 🔑 Identity & Context Fields

| Field | What it means | Example |
|-------|--------------|---------|
| `run_id` | Short unique ID for this run | `"b0496dc1"` |
| `project_id` | Full UUID of the project | `"1dde3dc6-97f8-..."` |
| `agent` | Which agent produced this | `"technical-document"` |
| `environment` | `development` or `production` | `"development"` |
| `app_version` | Version of the agent software | `"1.0.0"` |
| `triggered_by` | How it was started: `api` or `manual` | `"api"` |
| `timestamp` | When the run started (UTC) | `"2026-06-15T13:16:22+00:00"` |
| `completed_at` | When the run finished | `"2026-06-15T13:19:06+00:00"` |
| `status` | `success` or `failure` | `"success"` |
| `error_stage` | Which stage failed (if any) | `null` |

---

### 🖥️ `system` — Server/Machine Resources

This is unique to the Technical Agent — it monitors how much memory and CPU the process used.

| Field | What it means | Example |
|-------|--------------|---------|
| `platform` | Operating system | `"windows"` |
| `python_version` | Python version running the agent | `"3.14.3"` |
| `peak_memory_mb` | Highest RAM usage during the run (megabytes) | `694.7 MB` |
| `avg_memory_mb` | Average RAM usage | `611.3 MB` |
| `cpu_percent_avg` | Average CPU usage % (100% = 1 full core) | `7.8%` |
| `cpu_percent_peak` | Highest CPU spike (400% = 4 cores maxed) | `402.7%` |
| `sampling_interval_seconds` | How often the system stats were checked | `0.5` (every 0.5 seconds) |

**🧠 Simple Example:**  
`cpu_percent_peak: 402.7` means at peak, the agent was using ~4 CPU cores simultaneously (Python uses parallel threads during embedding/chunking).

---

### 🤖 `llm_usage` — Token Usage

| Field | What it means | Example |
|-------|--------------|---------|
| `total_prompt_tokens` | Tokens sent to AI across all calls | `11,744` |
| `total_completion_tokens` | Tokens the AI generated back | `2,763` |
| `total_tokens` | Grand total | `14,507` |
| `estimated_cost_usd` | Estimated cost | `$0.07668` (~7.7 cents) |
| `tokens_per_section` | Token breakdown per document section | See below |

**`tokens_per_section` example:**
```json
"Executive Summary": 7100,   ← this section needed more context (longer prompt)
"AI/ML Pipeline":   7407     ← similarly large
```

---

### 📥 `ingestion` — Reading the Source Code

| Field | What it means | Example |
|-------|--------------|---------|
| `source_type` | How the code was uploaded: `zip`, `git`, etc. | `"zip"` |
| `total_files_found` | Files found inside the ZIP | `4` |
| `files_after_filter` | Files remaining after filtering irrelevant ones | `4` |
| `filter_rate_percent` | % of files kept (100% = none were filtered out) | `100.0%` |
| `ingestion_duration_seconds` | Time to unzip and read the files | `0.1` seconds |
| `ingestion_success` | Did the ingestion step succeed? | `true` |

**`input_profile`** — A snapshot of the codebase:

| Field | What it means | Example |
|-------|--------------|---------|
| `total_loc` | Total Lines of Code in the repo | `1,011` |
| `primary_language` | The dominant programming language | `"JavaScript"` |
| `language_breakdown` | How many files per language | `{"JavaScript": 1, "Python": 1}` |
| `repo_size_kb` | Total size of the codebase | `83.6 KB` |

---

### 🧠 `context_building` — Making the AI Understand the Code

Before the AI can write documentation, it needs to "read" and "understand" the code. This is done by splitting the code into chunks and creating **embeddings** (mathematical representations of text).

| Field | What it means | Example |
|-------|--------------|---------|
| `strategy` | How the code was split: `flat` (simple chunking) or `raptor` (hierarchical) | `"flat"` |
| `total_chunks` | How many text chunks the codebase was split into | `49` |
| `embedding_duration_seconds` | Time to create vector embeddings | `4.51` seconds |
| `context_building_duration_seconds` | Same as above (total context prep time) | `4.51` seconds |
| `vector_store_size_mb` | Size of the in-memory vector database | `1.36 MB` |
| `raptor_summary_nodes` | Number of hierarchical summary nodes (0 if using flat strategy) | `0` |

**🧠 Simple Example:**  
Think of embedding as translating the code into a "searchable language" that the AI understands. 49 chunks = 49 paragraphs of code. When the AI needs to write about the "ML Pipeline," it searches the 49 chunks to find the most relevant ones.

---

### 🎯 `section_selection` — Which Doc Sections Were Written

The Technical Document has 18 possible sections (Executive Summary, API Reference, Architecture, etc.). The agent decides which ones are relevant based on the codebase.

| Field | What it means | Example |
|-------|--------------|---------|
| `total_sections_available` | Total sections the agent *could* write | `18` |
| `sections_selected` | How many were actually selected for this run | `2` |
| `selection_method` | How sections were chosen: `ai_suggested` or `manual` | `"ai_suggested"` |

---

### ✍️ `generation` — Writing the Document

| Field | What it means | Example |
|-------|--------------|---------|
| `sections_attempted` | How many sections the AI tried to write | `2` |
| `sections_succeeded` | How many were written successfully | `2` |
| `sections_failed` | How many failed | `0` |
| `section_success_rate_percent` | Success rate % | `100.0%` |
| `avg_quality_score` | Average content quality score (0–1) | `0.95` |
| `min_quality_score` | Lowest quality score for any section | `0.9` |
| `max_quality_score` | Highest quality score | `1.0` |
| `total_generation_duration_seconds` | Total AI writing time | `59.34` seconds |
| `llm_retries` | How many times the AI had to retry a section | `0` |
| `empty_sections` | Sections that came back with no content | `[]` (none empty) |
| `quality_scoring_method` | How quality was measured | `"heuristic_length_structure_keyword"` |
| `quality_score_scale` | Scale used for scoring | `"0_to_1"` |

**`per_section_scores`** — Quality per section:
```json
"Executive Summary": 0.9,   ← good but not perfect (heuristically shorter)
"AI/ML Pipeline": 1.0        ← perfect score
```

**`per_section_word_counts`** — How many words per section:
```json
"Executive Summary": 389 words
"AI/ML Pipeline":   1023 words
```

**🧠 Quality Score Explained:**  
The score uses a heuristic that checks: (1) Is the section long enough? (2) Does it have proper headings? (3) Does it contain relevant technical keywords? A score of `1.0` = all three checks passed perfectly.

---

### 🔧 `assembly` — Building the Final Document

| Field | What it means | Example |
|-------|--------------|---------|
| `output_file` | The output filename | `"output.docx"` |
| `output_size_bytes` | File size | `54,153` bytes (~53 KB) |
| `output_size_kb` | File size in kilobytes | `52.9 KB` |
| `word_count` | Total words in the final document | `1,412` |
| `page_estimate` | Estimated number of pages | `5` |
| `section_count` | Number of sections in the document | `2` |
| `assembly_duration_seconds` | Time to build the `.docx` file | `0.54` seconds |
| `assembly_success` | Did the assembly step succeed? | `true` |
| `output_validation_success` | Does the file pass validation? | `true` |
| `output_validation_error` | Error message if validation failed | `null` |

---

### 🔄 `review` — Human Review Tracking

| Field | What it means | Example |
|-------|--------------|---------|
| `review_cycles` | How many times the document was reviewed and sent back | `2` |
| `review_cycle_source` | Who triggered the review: `manual` or `automated` | `"manual"` |
| `review_duration_seconds` | Time spent in review (0 if tracked externally) | `0.0` |

---

### 🏅 `quality_metrics` — Deep Quality Analysis

This is the most detailed block — it analyzes the *accuracy* and *completeness* of the technical documentation.

#### `codebase_coverage` — How Much of the Code Was Documented?

| Field | What it means | Example |
|-------|--------------|---------|
| `discovered_apis` | API endpoints found in the code | `3` |
| `documented_apis` | API endpoints actually documented in the output | `1` |
| `discovered_classes` | Classes found in the code | `0` |
| `documented_classes` | Classes documented | `0` |
| `discovered_functions` | Functions/methods found in the code | `30` |
| `documented_functions` | Functions documented | `13` |
| `discovered_total` | Total discoverable items (APIs + classes + functions) | `33` |
| `documented_total` | Total items that appear in the document | `14` |
| `covered_total` | Items that were discovered AND documented | `14` |
| `overall_coverage_percent` | % of the codebase covered by documentation | `42.4%` |

**🧠 Simple Example:**  
The codebase has 30 functions, but the documentation only explains 13 of them. That's 43% coverage. Good documentation would aim for 70%+.

---

#### `tech_stack` — Did the Agent Correctly Identify the Tech Stack?

| Field | What it means | Example |
|-------|--------------|---------|
| `detected` | What the agent *thought* it found (file extension hints) | `{"JavaScript", "Python"}` |
| `actual` | What was *actually* in the code (confirmed by analysis) | Same |
| `correct_matches` | Technologies that were correctly detected | `[]` |
| `missed_items` | Technologies the agent missed | `["frameworks", "languages"]` |
| `false_positives` | Things the agent detected that weren't real | `["detected_framework_hints"]` |
| `accuracy_score` | How accurate the tech stack detection was | `0.0` |

**⚠️ Note:** `accuracy_score: 0.0` is common in current runs — this means the *comparison logic* hasn't been fully calibrated yet (the "detected" and "actual" fields use different key names), not necessarily that the agent failed.

---

#### `code_examples` — Are the Code Snippets in the Doc Valid?

The document includes code examples to illustrate concepts. These are validated for syntax correctness.

| Field | What it means | Example |
|-------|--------------|---------|
| `total_examples` | Total code snippets in the document | `8` |
| `valid_examples` | Snippets that pass syntax checking | `4` |
| `invalid_examples` | Snippets with syntax errors | `4` |
| `validation_method` | How snippets were validated | `"syntax_and_lint"` |
| `errors` | List of specific errors found | See below |
| `validity_score_percent` | % of valid code examples | `50.0%` |

**Error example:**
```json
{
  "section": "AI/ML Pipeline",
  "language": "python",
  "error": "Python SyntaxError: unexpected indent on line 1",
  "snippet_preview": "   df['attribute_ed'] = df[...].str.strip()..."
}
```
This means the code snippet had leading spaces that made it look like it was inside a function (Python cares about indentation). The agent extracted it out of context.

---

#### `acceptance_flag`

| Value | Meaning |
|-------|---------|
| `"accepted"` | A reviewer approved this document |
| `"not_reviewed"` | No human has reviewed it yet |
| `"rejected"` | Reviewer rejected it (needs rework) |

---

### ⏱️ `end_to_end_duration_seconds`

The true total time from the API request being received to the file being saved — this includes time between pipeline steps, startup overhead, etc.

Example: `164.02` seconds = ~2.7 minutes for the full end-to-end run.

---

## 📊 Quick Reference Summary Table

| Metric Category | BRD Agent | PPT Agent | Technical Agent |
|----------------|-----------|-----------|-----------------|
| Run Identity | ✅ `run_id`, `project_id` | ✅ `run_id` | ✅ `run_id`, `project_id` |
| Success/Failure | ✅ `run_outcome` | ✅ `run_success` | ✅ `status` |
| Timing | ✅ `timing` | ✅ `duration` | ✅ (calculated from timestamps) |
| LLM Token Usage | ✅ `llm_usage` (by stage) | ✅ `llm_tokens` (by phase) | ✅ `llm_usage` (by section) |
| Cost | ✅ `cost` object | ✅ `estimated_cost_usd` | ✅ in `llm_usage` |
| Section Quality | ✅ SMART + Completeness | ✅ Content quality score | ✅ Per-section scores |
| Conflict Handling | ✅ `conflicts` | ❌ N/A | ❌ N/A |
| Diagram Quality | ❌ N/A | ✅ `diagram` + coverage | ❌ N/A |
| File Health | ✅ `output` | ✅ `pptx_validation` | ✅ `assembly` |
| System Resources | ❌ N/A | ❌ N/A | ✅ `system` (CPU + RAM) |
| Codebase Coverage | ❌ N/A | ❌ N/A | ✅ `codebase_coverage` |
| Code Validation | ❌ N/A | ❌ N/A | ✅ `code_examples` |
| Acceptance Status | ✅ `acceptance` | ✅ `acceptance_status` | ✅ `acceptance_flag` |

---

## 💡 Key Insights for Your Presentation

1. **All three agents track cost** — BRD runs cost ~26 cents, PPT runs ~7.3 cents, Technical Doc runs ~7.7 cents. Total cost per project: well under $0.50.

2. **BRD quality is strong overall (93% completeness)** but measurability of requirements is low (~9–10%). This is a common finding — requirements rarely have KPIs attached upfront.

3. **PPT diagrams are the most variable metric** — some runs achieve 100% correctness, others as low as 62.5%. This is where quality improvements are most impactful.

4. **Technical documentation coverage averages 15–42%** — meaning the AI documents less than half of the codebase. This is expected for AI-generated docs and is a tuning opportunity.

5. **All runs currently show `acceptance_status: pending`** — no human review has been completed yet. This is the next step in the workflow.

---

*This README was generated based on code analysis of the `brd-agent`, `ai_solution_architect_v2`, and `technical-document` agent codebases and their respective JSON metric outputs.*
