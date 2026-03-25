from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.routes import ingest, sections, context, generation, assembly


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Documentation Agent API starting up...")
    yield
    print("Documentation Agent API shutting down...")


app = FastAPI(
    title="Documentation Agent",
    description="Automated technical documentation generation from codebases.",
    version="1.0.0",
    lifespan=lifespan,
)


app.include_router(ingest.router,      prefix="/ingest",     tags=["1. Ingestion"])
app.include_router(sections.router,    prefix="/sections",   tags=["2. Section Selection"])
app.include_router(context.router,     prefix="/context",    tags=["3. Context Building"])
app.include_router(generation.router,  prefix="/generate",   tags=["4. Generation"])
app.include_router(assembly.router, prefix="/api", tags=["assembly"])



@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "Documentation Agent"}
