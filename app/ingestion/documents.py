"""Safe parsing and deterministic chunking for PDF, text, and Markdown uploads."""

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown"}


class DocumentError(ValueError):
    """Raised when a document cannot be safely parsed or indexed."""


@dataclass(frozen=True)
class PageText:
    page: int
    text: str


@dataclass(frozen=True)
class Chunk:
    text: str
    document_id: str
    filename: str
    page: int | None
    section: str | None
    chunk_index: int


def document_id(filename: str, content: bytes) -> str:
    """Content-addressed identity means re-uploading the same file is idempotent."""
    digest = hashlib.sha256(content).hexdigest()
    return f"{Path(filename).name}:{digest}"


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ").replace("\u00ad", "")
    text = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_document(filename: str, content: bytes) -> list[PageText]:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise DocumentError("Only PDF, TXT, and Markdown files are supported.")
    if not content:
        raise DocumentError("The uploaded file is empty.")
    if suffix == ".pdf":
        try:
            import fitz

            with fitz.open(stream=content, filetype="pdf") as pdf:
                pages = [PageText(i + 1, clean_text(page.get_text("text"))) for i, page in enumerate(pdf)]
        except Exception as exc:
            raise DocumentError("Could not read this PDF. It may be malformed or encrypted.") from exc
        if not pages or not any(p.text for p in pages):
            raise DocumentError("No selectable text found. This PDF may be scanned; OCR is not enabled yet.")
        return pages
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DocumentError("Text documents must use UTF-8 encoding.") from exc
    text = clean_text(text)
    if not text:
        raise DocumentError("No readable text was found in this file.")
    return [PageText(1, text)]


def chunk_pages(
    pages: list[PageText], *, filename: str, doc_id: str, chunk_size: int, overlap: int
) -> list[Chunk]:
    if chunk_size < 1 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("Require chunk_size > overlap >= 0")
    chunks: list[Chunk] = []
    index = 0
    for page in pages:
        text = page.text
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            if end < len(text):
                boundary = text.rfind(" ", start, end)
                if boundary > start + chunk_size // 2:
                    end = boundary
            piece = text[start:end].strip()
            if piece:
                chunks.append(Chunk(piece, doc_id, Path(filename).name, page.page, None, index))
                index += 1
            if end >= len(text):
                break
            start = max(start + 1, end - overlap)
    return chunks
