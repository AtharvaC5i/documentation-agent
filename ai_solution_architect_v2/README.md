# AI Solution Architect

Transforms BRDs and Technical Documentation into architecture, diagrams, slides, and production-ready code — powered by Databricks Model Serving (Claude Sonnet).

## Directory Structure

```
architect/
├── backend/
│   ├── main.py                        # FastAPI app entry point
│   ├── requirements.txt
│   ├── .env.example                   # Copy to .env and fill values
│   ├── routers/
│   │   └── generate.py                # POST /api/v1/generate
│   ├── models/
│   │   ├── request_models.py          # Pydantic input models
│   │   └── response_models.py         # Pydantic output models
│   ├── services/
│   │   ├── databricks_client.py       # Async Databricks REST client
│   │   └── orchestrator.py            # Agent pipeline orchestration
│   ├── agents/
│   │   └── prompt_builder.py          # System prompt + user message builder
│   └── utils/                         # (extend as needed)
│
└── frontend/
    ├── app.py                         # Streamlit UI
    └── requirements.txt
```

## Setup

### 1. Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your Databricks credentials

export $(cat .env | xargs)
uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
pip install -r requirements.txt

export ARCHITECT_API_URL=http://localhost:8000/api/v1
streamlit run app.py
```

## Environment Variables

| Variable               | Description                                      |
|------------------------|--------------------------------------------------|
| `DATABRICKS_HOST`      | e.g. `https://adb-xxx.azuredatabricks.net`      |
| `DATABRICKS_TOKEN`     | Databricks personal access token                 |
| `DATABRICKS_ENDPOINT`  | Model serving endpoint name                      |
| `ARCHITECT_API_URL`    | Frontend → Backend URL (default: localhost:8000) |

## API Endpoints

| Method | Path                       | Description                         |
|--------|----------------------------|-------------------------------------|
| GET    | /health                    | Health check                        |
| POST   | /api/v1/generate           | Submit BRD + tech doc as form text  |
| POST   | /api/v1/generate-file      | Submit BRD + tech doc as file upload|
