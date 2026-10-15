from types import SimpleNamespace

import app.retrieval.store as store
from app.ingestion.documents import Chunk


def test_qdrant_index_search_reindex_and_delete(monkeypatch, tmp_path):
    settings = SimpleNamespace(data_dir=tmp_path, qdrant_url=None, qdrant_api_key=None,
                              qdrant_collection="test_collection", top_k=3)
    monkeypatch.setattr(store, "get_settings", lambda: settings)
    monkeypatch.setattr(store, "dimension", lambda: 3)
    monkeypatch.setattr(store, "encode", lambda texts: [[1.0, 0.0, 0.0] for _ in texts])
    store.get_client.cache_clear()
    try:
        chunk = Chunk("attention is all you need", "paper:hash", "paper.txt", 2, None, 0)
        assert store.index_chunks([chunk]) == 1
        assert store.index_chunks([chunk]) == 1
        results = store.search("attention mechanism")
        assert len(results) == 1
        assert results[0]["filename"] == "paper.txt"
        assert results[0]["page"] == 2
        assert store.list_documents() == [{"document_id": "paper:hash", "filename": "paper.txt"}]
        store.delete_document("paper:hash")
        assert store.search("attention mechanism") == []
    finally:
        store.get_client().close()
        store.get_client.cache_clear()
