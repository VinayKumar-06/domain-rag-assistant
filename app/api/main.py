"""FastAPI entry point for ingestion, deletion, retrieval, and grounded Q&A."""

import logging
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.config import get_settings
from app.generation.answer import generate_answer
from app.ingestion.documents import DocumentError, chunk_pages, document_id, parse_document
from app.retrieval.store import delete_document, index_chunks, list_documents, search

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)
app = FastAPI(title="Domain RAG Assistant", version="0.1.0")


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/documents")
def documents():
    return {"documents": list_documents()}


@app.post("/documents", status_code=201)
async def upload_document(file: UploadFile = File(...)):
    settings = get_settings()
    filename = Path(file.filename or "upload").name
    if Path(filename).suffix.lower() not in {".pdf", ".txt", ".md", ".markdown"}:
        raise HTTPException(415, "Supported formats: PDF, TXT, Markdown.")
    content = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds the {settings.max_upload_mb} MB limit.")
    try:
        pages = parse_document(filename, content)
        doc_id = document_id(filename, content)
        chunks = chunk_pages(pages, filename=filename, doc_id=doc_id,
                             chunk_size=settings.chunk_size, overlap=settings.chunk_overlap)
        count = index_chunks(chunks)
    except DocumentError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        logger.exception("Document indexing failed: %s", filename)
        raise HTTPException(503, "Indexing failed. Check server logs and service configuration.") from exc
    return {"document_id": doc_id, "filename": filename, "chunks_indexed": count,
            "pages_read": len(pages), "status": "indexed"}


@app.delete("/documents/{doc_id}")
def remove_document(doc_id: str):
    try:
        delete_document(doc_id)
    except Exception as exc:
        logger.exception("Document deletion failed")
        raise HTTPException(503, "Could not delete document.") from exc
    return {"document_id": doc_id, "status": "deleted"}


@app.post("/ask")
def ask(request: AskRequest):
    started = perf_counter()
    try:
        passages = search(request.question, request.top_k)
        answer, sources = generate_answer(request.question, passages)
    except Exception as exc:
        logger.exception("Question answering failed")
        raise HTTPException(503, "Question answering is temporarily unavailable.") from exc
    return {"answer": answer, "sources": sources,
            "latency_ms": round((perf_counter() - started) * 1000, 1)}
