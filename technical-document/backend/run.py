import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        reload_excludes=["storage/*", "*.pyc", "__pycache__", "venv/*"],
    )
