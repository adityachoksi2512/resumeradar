# ResumeRadar

AI-powered resume screening pipeline. Upload a job description and candidate resumes — get a ranked shortlist with scores, matched skills, and AI-written candidate briefs instantly.

Works for any role. No hardcoded domain knowledge. JD-driven scoring powered by Claude.

---

## Demo

1. Upload a JD (PDF or Word)
2. Upload candidate resumes (PDF or Word, multiple files)
3. Click **Screen candidates**
4. Get a ranked shortlist with scores and skill match highlights
5. Click **Generate candidate briefs with AI** for plain-English summaries

Tested across ML Engineer, Data Analyst, Senior Barista, and Scuba Diving Instructor roles.

---

## How it works

**JD parsing** — Claude reads the uploaded JD and extracts required skills, minimum experience, and degree requirements. No hardcoded role configs.

**Resume parsing** — Each resume is parsed concurrently using asyncio. Skills are matched dynamically against what the JD specified — not a fixed list.

**Scoring** — Each candidate is scored 0–100 using a weighted formula:
- Skill match (50%) — % of required skills found in the resume
- Experience (30%) — years relative to the JD minimum
- Degree (20%) — whether degree requirement is met

**Shortlist threshold** — 60 for standard candidates, 50 for senior candidates.

**Agent briefs** — Claude writes a 3–4 sentence plain-English brief for each shortlisted candidate covering strengths, fit, and any gaps.

---

## Tech stack

| Layer | Technology | Role |
|---|---|---|
| OOP | Python | `Resume`, `Candidate`, `SeniorCandidate`, `Scorer` classes |
| Data processing | Pandas | CSV ingestion and EDA for the training dataset |
| API | FastAPI + Pydantic | REST backend — `/extract`, `/parse-jd`, `/screen-dynamic`, `/agent-summary` |
| Concurrency | asyncio + ThreadPoolExecutor | Concurrent resume parsing in the live request path |
| Containerization | Docker | Portable API image deployable to Cloud Run |
| Pipeline | Prefect | Offline ML pipeline — ingest → featurize → train → evaluate → save |
| Agents | Google ADK + Claude | JD parsing and candidate brief generation |

---

## Project structure

```
resumeradar/
├── api/
│   ├── main.py              # FastAPI app and all endpoints
│   ├── schemas.py           # Pydantic request/response models
│   └── auth.py              # API key header validation
├── agents/
│   ├── recruiter_agent.py   # ADK agent — screens via API
│   ├── summarizer_agent.py  # Claude — writes candidate briefs
│   └── orchestrator.py      # Runs both agents in sequence
├── core/
│   ├── async_parser.py      # Concurrent resume file parsing
│   ├── parallel_scorer.py   # ThreadPoolExecutor scoring
│   ├── file_parser.py       # PDF and Word text extraction
│   └── jd_parser.py         # Claude-powered JD parsing
├── etl/
│   └── data_processor.py    # Pandas data loading and EDA
├── models/
│   ├── resume.py            # Resume class — dynamic skill extraction
│   ├── candidate.py         # Candidate and SeniorCandidate classes
│   └── scorer.py            # Role-agnostic weighted scorer
├── pipeline/
│   ├── components.py        # Prefect tasks
│   └── pipeline.py          # Prefect flow
├── data/
│   └── sample_resumes.csv   # Sample dataset
├── test files/              # Sample JDs and resumes for testing
├── index.html               # Frontend demo UI
├── Dockerfile               # Container definition
└── requirements.txt
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
pip install anthropic pymupdf python-docx google-adk python-multipart prefect
```

### 2. Set your API key

```bash
# Windows
set ANTHROPIC_API_KEY=your_key_here

# Mac/Linux
export ANTHROPIC_API_KEY=your_key_here
```

Get a free key at [console.anthropic.com](https://console.anthropic.com).

---

## Running

### Terminal 1 — Start the API

```bash
set ANTHROPIC_API_KEY=your_key_here
uvicorn api.main:app --reload
```

API docs at `http://127.0.0.1:8000/docs`

### Terminal 2 — Start the UI

```bash
python -m http.server 5500
```

Open `http://localhost:5500`

### Docker

```bash
docker build -t resumeradar .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=your_key_here resumeradar
```

### Prefect pipeline

```bash
python -m pipeline.pipeline
```

### ADK agents (terminal only)

```bash
python -m agents.orchestrator
```

---

## API reference

### `GET /`
Health check.

### `GET /roles`
List available static roles.

### `POST /parse-jd`
Upload a JD file and get back extracted criteria (role, skills, experience, degree).

### `POST /screen-dynamic`
Full pipeline — upload JD + resumes, get ranked shortlist. Accepts multipart form data.

### `POST /agent-summary`
Send screening results, get back AI-written candidate briefs.

### `POST /screen`
Screen against a static role config. Requires `x-api-key: radar-key-2024` header.

---

## Test files

Sample JDs and resumes are included in `test files/` covering four domains:

| Domain | JD | Resumes |
|---|---|---|
| ML Engineer | `JD_ML_Engineer.docx` | David Moore, Sarah Chen, James Patel, Priya Nair, Alex Kim |
| Data Analyst | `JD_Data_Analyst.docx` | — |
| Senior Barista | `JD_Senior_Barista.docx` | Maya Johnson, Carlos Rivera, Tanya Williams, Jake Thompson |
| Scuba Instructor | `JD_Scuba_Instructor.docx` | Marco Reyes, Lena Fischer, Tom Bradley, Nina Patel, Kevin O'Brien |
