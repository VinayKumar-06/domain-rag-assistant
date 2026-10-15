import json

from evaluation.run import evaluate


def test_recall_and_mrr_use_reviewed_chunk_ids(monkeypatch, tmp_path):
    questions = [
        {"question": "First?", "relevant_chunk_ids": ["doc:1"], "answerable": True},
        {"question": "Second?", "relevant_chunk_ids": ["other:9"], "answerable": True},
        {"question": "Not present?", "relevant_chunk_ids": [], "answerable": False},
    ]
    data = tmp_path / "questions.jsonl"
    data.write_text("\n".join(json.dumps(item) for item in questions))
    monkeypatch.setattr("evaluation.run.search", lambda question, top_k: [
        {"document_id": "doc", "chunk_index": 4}, {"document_id": "doc", "chunk_index": 1}
    ] if question == "First?" else [{"document_id": "doc", "chunk_index": 4}])
    result = evaluate(data, top_k=2)
    assert result["questions"] == 3
    assert result["answerable_questions"] == 2
    assert result["recall_at_k"] == 0.5
    assert result["mrr"] == 0.25
