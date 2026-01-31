"""
Web UI for Medical Paper Summarizer.
Run with: python web_server.py
"""
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse

from summarization.summarizer import MedicalPaperSummarizer

app = FastAPI(title="Medical Paper Summarizer", version="1.0")

# Create summarizer on startup (lazy init to avoid loading before API keys checked)
_summarizer: MedicalPaperSummarizer | None = None


def get_summarizer() -> MedicalPaperSummarizer:
    """Lazy-initialize summarizer."""
    global _summarizer
    if _summarizer is None:
        _summarizer = MedicalPaperSummarizer()
    return _summarizer


@app.get("/health")
async def health():
    """Health check for deployment platforms."""
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main UI."""
    html_path = Path(__file__).parent / "static" / "index.html"
    return html_path.read_text(encoding="utf-8")


@app.post("/summarize")
async def summarize_paper(file: UploadFile = File(...)):
    """
    Upload a PDF file and receive an AI-generated summary.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    suffix = Path(file.filename).suffix.lower()
    if suffix != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported. Please upload a .pdf file.",
        )

    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        summarizer = get_summarizer()
        summary = summarizer.summarize(tmp_path)
        return {
            "markdown": summary.to_markdown(),
            "title": summary.title,
            "json": summary.model_dump(mode="json"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def main():
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
