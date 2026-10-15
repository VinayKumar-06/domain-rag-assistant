"""Qdrant-backed vector store; local persistent mode is the zero-service default."""

from functools import lru_cache
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient, models

from app.config import get_settings
from app.embeddings.model import dimension, encode
from app.ingestion.documents import Chunk


@lru_cache
def get_client() -> QdrantClient:
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    if settings.qdrant_url:
        return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    return QdrantClient(path=str(settings.data_dir / "qdrant"))


def ensure_collection() -> None:
    client = get_client()
    name = get_settings().qdrant_collection
    if not client.collection_exists(name):
        client.create_collection(
            collection_name=name,
            vectors_config=models.VectorParams(size=dimension(), distance=models.Distance.COSINE),
        )


def index_chunks(chunks: list[Chunk]) -> int:
    if not chunks:
        return 0
    ensure_collection()
    vectors = encode([chunk.text for chunk in chunks])
    points = []
    for chunk, vector in zip(chunks, vectors, strict=True):
        key = f"{chunk.document_id}:{chunk.chunk_index}"
        points.append(models.PointStruct(
            id=str(uuid5(NAMESPACE_URL, key)), vector=vector,
            payload={"text": chunk.text, "document_id": chunk.document_id,
                     "filename": chunk.filename, "page": chunk.page,
                     "section": chunk.section, "chunk_index": chunk.chunk_index},
        ))
    get_client().upsert(collection_name=get_settings().qdrant_collection, points=points, wait=True)
    return len(points)


def search(query: str, top_k: int | None = None) -> list[dict]:
    ensure_collection()
    result = get_client().query_points(
        collection_name=get_settings().qdrant_collection,
        query=encode([query])[0], limit=top_k or get_settings().top_k,
        with_payload=True,
    )
    return [{**(point.payload or {}), "score": float(point.score)} for point in result.points]


def delete_document(doc_id: str) -> None:
    if get_client().collection_exists(get_settings().qdrant_collection):
        get_client().delete(
            collection_name=get_settings().qdrant_collection,
            points_selector=models.FilterSelector(
                filter=models.Filter(must=[models.FieldCondition(
                    key="document_id", match=models.MatchValue(value=doc_id)
                )])
            ), wait=True,
        )


def list_documents() -> list[dict]:
    name = get_settings().qdrant_collection
    client = get_client()
    if not client.collection_exists(name):
        return []
    docs: dict[str, dict] = {}
    offset = None
    while True:
        points, offset = client.scroll(collection_name=name, offset=offset, limit=256,
                                       with_payload=True, with_vectors=False)
        for point in points:
            payload = point.payload or {}
            docs[payload["document_id"]] = {"document_id": payload["document_id"],
                                           "filename": payload["filename"]}
        if offset is None:
            break
    return list(docs.values())
