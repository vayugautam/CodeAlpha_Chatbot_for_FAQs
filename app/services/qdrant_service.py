"""Qdrant Cloud connection and FAQ collection management."""
import os
from functools import lru_cache

from qdrant_client import QdrantClient, models

from app.services.embedding_service import DIMENSIONS

COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "codealpha_faq_knowledge_base")


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    url, key = os.getenv("QDRANT_URL", "").strip(), os.getenv("QDRANT_API_KEY", "").strip()
    if not url or not key:
        raise RuntimeError("QDRANT_URL and QDRANT_API_KEY are required for Qdrant Cloud")
    return QdrantClient(url=url, api_key=key, timeout=30)


def ensure_collection(client: QdrantClient | None = None) -> None:
    client = client or get_qdrant_client()
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(collection_name=COLLECTION_NAME, vectors_config=models.VectorParams(size=DIMENSIONS, distance=models.Distance.COSINE))
    info = client.get_collection(COLLECTION_NAME)
    config = info.config.params.vectors
    if not isinstance(config, models.VectorParams) or config.size != DIMENSIONS or config.distance != models.Distance.COSINE:
        raise ValueError(f"Qdrant collection {COLLECTION_NAME} must be a single 3072-dimensional cosine vector collection")
    index_types = {"faq_id": models.PayloadSchemaType.KEYWORD, "source_file": models.PayloadSchemaType.KEYWORD}
    schema = info.payload_schema or {}
    for field, field_type in index_types.items():
        existing = schema.get(field)
        if existing is None:
            client.create_payload_index(collection_name=COLLECTION_NAME, field_name=field, field_type=field_type, wait=True)
        elif existing.data_type != field_type:
            raise ValueError(f"Qdrant payload index {field} has unexpected type {existing.data_type}")


def upsert(points: list[models.PointStruct], client: QdrantClient | None = None) -> None:
    ensure_collection(client)
    if points:
        (client or get_qdrant_client()).upsert(collection_name=COLLECTION_NAME, points=points, wait=True)
