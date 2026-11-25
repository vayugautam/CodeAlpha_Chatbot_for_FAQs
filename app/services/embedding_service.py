"""Gemini embedding client with reusable client and dimension validation."""
import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()
DIMENSIONS = int(os.getenv("GEMINI_EMBEDDING_DIMENSIONS", "3072"))
MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
if DIMENSIONS != 3072:
    raise ValueError("GEMINI_EMBEDDING_DIMENSIONS must be 3072")


@lru_cache(maxsize=1)
def get_client():
    from google import genai
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GEMINI_API_KEY must be configured")
    return genai.Client(api_key=key)


def generate_embedding(text: str) -> list[float]:
    if not text.strip():
        raise ValueError("Cannot embed empty text")
    response = get_client().models.embed_content(
        model=MODEL, contents=text,
        config={"output_dimensionality": DIMENSIONS, "task_type": "RETRIEVAL_DOCUMENT"},
    )
    vectors = getattr(response, "embeddings", None) or []
    values = list(vectors[0].values) if vectors else []
    if len(values) != DIMENSIONS:
        raise ValueError(f"Gemini returned {len(values)} embedding dimensions; expected {DIMENSIONS}")
    return values


def generate_query_embedding(text: str) -> list[float]:
    if not text.strip():
        raise ValueError("Cannot embed empty text")
    response = get_client().models.embed_content(
        model=MODEL, contents=text,
        config={"output_dimensionality": DIMENSIONS, "task_type": "RETRIEVAL_QUERY"},
    )
    values = list(response.embeddings[0].values) if response.embeddings else []
    if len(values) != DIMENSIONS:
        raise ValueError(f"Gemini returned {len(values)} embedding dimensions; expected {DIMENSIONS}")
    return values
