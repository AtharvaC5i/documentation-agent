from dotenv import load_dotenv
load_dotenv()
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import generate


app = FastAPI(
    title="AI Solution Architect API",
    description="Transforms BRDs and Technical Docs into architecture, diagrams, slides, and code.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router, prefix="/api/v1", tags=["Generate"])

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "AI Solution Architect API"}
