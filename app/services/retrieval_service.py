"""Semantic FAQ retrieval from the shared Qdrant Cloud collection."""
import os

from qdrant_client import models

from app.services.embedding_service import generate_query_embedding
from app.services.qdrant_service import COLLECTION_NAME, ensure_collection, get_qdrant_client


def retrieve(question: str) -> list[dict]:
    client = get_qdrant_client()
    ensure_collection(client)
    top_k = int(os.getenv("RETRIEVAL_TOP_K", "5"))
    threshold = float(os.getenv("RETRIEVAL_SCORE_THRESHOLD", "0.50"))
    response = client.query_points(collection_name=COLLECTION_NAME, query=generate_query_embedding(question), limit=top_k, with_payload=True, score_threshold=threshold)
    return [{**(point.payload or {}), "similarity": float(point.score)} for point in response.points]
