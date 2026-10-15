"""Answers that use only actual retrieved passages and verifiable source labels."""

import re

import httpx

from app.config import get_settings

SYSTEM_PROMPT = """Answer only from the supplied evidence. If it does not support a useful answer,
say: 'I don't know based on the indexed documents.' Do not use outside knowledge. Cite evidence
inline as [S1], [S2]. If sources conflict, describe the conflict and cite both. Never invent a source."""


def generate_answer(question: str, passages: list[dict]) -> tuple[str, list[dict]]:
    if not passages:
        return "I don't know based on the indexed documents; no relevant passages were retrieved.", []
    sources = []
    evidence = []
    for i, p in enumerate(passages, start=1):
        source = {"id": f"S{i}", "filename": p["filename"], "page": p.get("page"),
                  "text": p["text"], "score": p.get("score")}
        sources.append(source)
        evidence.append(f"[S{i}] {p['filename']} (page {p.get('page') or 'unknown'}):\n{p['text']}")
    settings = get_settings()
    if not (settings.llm_base_url and settings.llm_model):
        answer = "I found these potentially relevant passages. Configure an LLM provider to synthesize an answer."
        return answer, sources
    response = httpx.post(
        f"{settings.llm_base_url.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {settings.llm_api_key or ''}"},
        json={"model": settings.llm_model, "temperature": 0,
              "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                           {"role": "user", "content": f"Question: {question}\n\nEvidence:\n" + "\n\n".join(evidence)}]},
        timeout=60,
    )
    response.raise_for_status()
    answer = response.json()["choices"][0]["message"]["content"].strip()
    allowed = {source["id"] for source in sources}
    cited = set(re.findall(r"\[(S\d+)\]", answer))
    answer = re.sub(r"\[(S\d+)\]", lambda match: match.group(0) if match.group(1) in allowed else "", answer)
    if not cited.intersection(allowed):
        answer = "I couldn't produce an answer with verifiable citations. Please review the retrieved passages."
    return answer, sources
