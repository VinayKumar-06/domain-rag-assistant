from fastapi.testclient import TestClient

from app.api import main

client = TestClient(main.app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_rejects_unsupported_file_before_indexing():
    response = client.post("/documents", files={"file": ("payload.exe", b"not executable")})
    assert response.status_code == 415


def test_upload_rejects_oversized_file(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setattr(main, "get_settings", lambda: SimpleNamespace(max_upload_mb=1))
    response = client.post("/documents", files={"file": ("notes.txt", b"x" * (1024 * 1024 + 1))})
    assert response.status_code == 413


def test_question_schema_rejects_short_input():
    response = client.post("/ask", json={"question": "?"})
    assert response.status_code == 422


def test_api_connects_parsing_indexing_retrieval_and_sources(monkeypatch):
    indexed = {}

    def fake_index(chunks):
        indexed["chunks"] = chunks
        return len(chunks)

    monkeypatch.setattr(main, "index_chunks", fake_index)
    response = client.post("/documents", files={"file": ("notes.md", b"Model cards document model limits.")})
    assert response.status_code == 201
    result = response.json()
    assert result["chunks_indexed"] == 1
    assert indexed["chunks"][0].filename == "notes.md"

    monkeypatch.setattr(main, "search", lambda question, top_k: [{
        "filename": "notes.md", "page": 1, "text": "Model cards document model limits.", "score": 0.9
    }])
    monkeypatch.setattr(main, "generate_answer", lambda question, passages: (
        "Model cards document model limits. [S1]", [{"id": "S1", "filename": "notes.md", "page": 1,
                                                      "text": passages[0]["text"]}]))
    answer = client.post("/ask", json={"question": "What do model cards document?"})
    assert answer.status_code == 200
    assert answer.json()["sources"][0]["filename"] == "notes.md"
