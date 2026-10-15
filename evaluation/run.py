"""Compute retrieval Recall@k and MRR from a reviewed JSONL question set."""

import json
from pathlib import Path

from app.retrieval.store import search


def evaluate(path: Path, top_k: int) -> dict:
    questions = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if not questions:
        raise SystemExit("No evaluation examples found. Add reviewed rows to evaluation/questions.jsonl.")
    recall_hits = 0
    reciprocal_ranks = []
    answerable_count = 0
    for item in questions:
        relevant = set(item.get("relevant_chunk_ids", []))
        results = search(item["question"], top_k)
        retrieved = [f"{r['document_id']}:{r['chunk_index']}" for r in results]
        if not item.get("answerable", True):
            continue
        answerable_count += 1
        recall_hits += int(bool(relevant.intersection(retrieved)))
        rank = next((i for i, chunk_id in enumerate(retrieved, start=1) if chunk_id in relevant), None)
        reciprocal_ranks.append(1 / rank if rank else 0.0)
    if answerable_count == 0:
        raise SystemExit("The dataset has no answerable questions.")
    return {"questions": len(questions), "answerable_questions": answerable_count,
            "top_k": top_k, "recall_at_k": recall_hits / answerable_count,
            "mrr": sum(reciprocal_ranks) / answerable_count}


if __name__ == "__main__":
    data_path = Path("evaluation/questions.jsonl")
    if not data_path.exists():
        raise SystemExit("Create evaluation/questions.jsonl first; results are never fabricated.")
    for k in (3, 5, 8):
        try:
            print(json.dumps(evaluate(data_path, k), indent=2))
        except Exception as exc:
            raise SystemExit(f"Evaluation stopped: {exc}") from exc
