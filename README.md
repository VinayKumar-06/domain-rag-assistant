---
title: Domain RAG Assistant
emoji: 📚
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Domain RAG Assistant

A small, explainable question-answering app for a curated collection of ML papers, technical documentation, and learning notes. It parses PDF, TXT, and Markdown files, indexes chunks in Qdrant, retrieves evidence, and can send that evidence to an OpenAI-compatible chat completions endpoint. Answers expose source passages with filenames and page numbers. If nothing is retrieved, it abstains; review the returned passages because semantic search can still return weakly related text.

> This is a portfolio project, not a source of authoritative research or professional advice. Check the original documents before relying on an answer.

## Quick start

Requires Python 3.11–3.14. Python 3.11 is used in CI and Docker. The pinned direct dependencies were selected from current package releases and their supported Python ranges; install them in a virtual environment.

```bash
cp .env.example .env
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.api.main:app --reload
```

In another terminal, run the interface:

```bash
source .venv/bin/activate
streamlit run ui/streamlit_app.py
```

Open `http://localhost:8501`. The FastAPI docs are at `http://localhost:8000/docs`. On first indexing, Sentence Transformers downloads the configured model; model download and indexing are CPU-bound in the default configuration.

## Configure answer generation

Set `LLM_BASE_URL`, `LLM_MODEL`, and optionally `LLM_API_KEY` in `.env` for a compatible `/chat/completions` service. Keep secrets out of Git. Without an LLM configured, the app still retrieves and displays evidence, but does not compose a natural-language answer. Provider failures return an API error rather than an invented response.

## Documents and safety

- Supported types: PDF, UTF-8 text, and Markdown. The API checks extension, request size, and parse errors.
- A textless PDF is reported as likely scanned; OCR is not enabled in this baseline.
- Documents are content-addressed and re-indexing produces the same vector IDs.
- Delete a document in the sidebar or through `DELETE /documents/{document_id}`.
- Do not upload private or copyrighted material unless you have permission. For hosted use, use private storage and appropriate access controls.

## Docker

```bash
cp .env.example .env
docker compose up --build
```

The UI listens on port 8501 and the API on 8000. Qdrant and application data use named Docker volumes. Back up those volumes or retain the source documents so the index can be rebuilt.

## Tests, lint, and evaluation

```bash
make test
make lint
```

Evaluation is intentionally not pre-populated with made-up benchmark rows. Review and add questions using `evaluation/README.md`, index the matching corpus, then run `make evaluate`. The script reports retrieval Recall@k and MRR at k=3, 5, and 8. Record corpus version, question-set version, hardware, embedding model, and date beside the output. Answer correctness and citation support require human-reviewed labels before reporting those metrics.

## Hugging Face Spaces

Create a Docker Space and push this repository. The container starts the Streamlit UI on port 7860 and the FastAPI service on an internal port. Set Space secrets/variables for the LLM provider and external Qdrant service. Do not rely on the Space's writable filesystem for durable documents or vectors. Persistent external Qdrant storage is recommended for a multi-session demo.

## Project map

- `app/ingestion/documents.py`: parsing, cleanup, content IDs, and overlapping chunks.
- `app/embeddings/model.py`: lazy CPU embedding model wrapper.
- `app/retrieval/store.py`: Qdrant collection, deterministic indexing, search, and deletion.
- `app/generation/answer.py`: grounded provider prompt and evidence-only fallback.
- `app/api/main.py`: validated upload, delete, health, and question endpoints.
- `ui/streamlit_app.py`: document manager and chat interface.
- `evaluation/`: reviewed data format and retrieval metrics.
- `docs/architecture.md`: component and persistence choices.

## Known limitations and next steps

The current retriever is dense semantic search; BM25, hybrid fusion, and reranking are follow-up improvements that should be compared on a reviewed question set. PDF layout and tables may be lost during text extraction. Scanned PDFs are detected but need an OCR pipeline. The app does not yet authenticate users, so do not expose it with sensitive documents. Generated citation labels are restricted to IDs from the retrieved passages, and an answer without a valid label is rejected; this checks citation identity, not whether the cited passage truly supports each claim. Measure semantic citation support before treating answers as reliable.
