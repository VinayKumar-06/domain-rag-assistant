"""Lazy sentence-transformers wrapper to avoid loading a model during API startup."""

from functools import lru_cache

from app.config import get_settings


@lru_cache
def get_encoder():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(get_settings().embedding_model, device="cpu")


def encode(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    vectors = get_encoder().encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return vectors.tolist()


def dimension() -> int:
    return int(get_encoder().get_embedding_dimension())
