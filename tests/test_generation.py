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


def test_provider_cannot_return_unretrieved_citation(monkeypatch):
    from types import SimpleNamespace
    import app.generation.answer as answer_module

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "A claim [S1] and a fake [S8]."}}]}

    monkeypatch.setattr(answer_module, "get_settings", lambda: SimpleNamespace(
        llm_base_url="http://local/v1", llm_model="demo", llm_api_key=None
    ))
    monkeypatch.setattr(answer_module.httpx, "post", lambda *args, **kwargs: Response())
    answer, sources = answer_module.generate_answer("Question?", [{"filename": "paper.pdf",
        "page": 1, "text": "Evidence", "score": 0.8}])
    assert answer == "A claim [S1] and a fake ."
    assert [source["id"] for source in sources] == ["S1"]


def test_provider_answer_without_citation_is_rejected(monkeypatch):
    from types import SimpleNamespace
    import app.generation.answer as answer_module

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "An uncited claim."}}]}

    monkeypatch.setattr(answer_module, "get_settings", lambda: SimpleNamespace(
        llm_base_url="http://local/v1", llm_model="demo", llm_api_key=None
    ))
    monkeypatch.setattr(answer_module.httpx, "post", lambda *args, **kwargs: Response())
    answer, _ = answer_module.generate_answer("Question?", [{"filename": "paper.pdf",
        "page": 1, "text": "Evidence", "score": 0.8}])
    assert "verifiable citations" in answer
