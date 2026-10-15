from app.generation.answer import generate_answer


def test_empty_evidence_abstains_without_sources():
    answer, sources = generate_answer("What is in the paper?", [])
    assert "don't know" in answer.lower()
    assert sources == []


def test_sources_are_built_from_retrieved_passages():
    answer, sources = generate_answer("Question?", [{"filename": "paper.pdf", "page": 4,
                                                       "text": "Evidence text", "score": 0.8}])
    assert "Configure an LLM" in answer
    assert sources[0]["filename"] == "paper.pdf"
    assert sources[0]["page"] == 4
