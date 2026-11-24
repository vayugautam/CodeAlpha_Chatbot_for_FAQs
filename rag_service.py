"""Retrieval-augmented FAQ answering with Gemini, Qdrant, and Groq."""
from __future__ import annotations

import json
import logging
import os
import uuid
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types
from groq import Groq
from qdrant_client import QdrantClient, models

logger = logging.getLogger(__name__)
EMBEDDING_DIMENSION = 768
POINT_NAMESPACE = uuid.UUID("6a47a03d-72a8-48db-9ef5-3a7ec3ad1e9a")


class FAQRAGService:
    """Indexes FAQ knowledge in Qdrant and generates grounded answers with Groq."""

    def __init__(self, faq_file_path: str = "faqs.json") -> None:
        self.faq_file_path = Path(faq_file_path)
        self.embedding_model = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
        self.llm_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        self.collection_name = os.getenv("QDRANT_COLLECTION", "cloudify_faq_knowledge")
        self.top_k = int(os.getenv("RETRIEVAL_TOP_K", "4"))
        self.score_threshold = float(os.getenv("RETRIEVAL_SCORE_THRESHOLD", "0.35"))

        gemini_key = os.getenv("GEMINI_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        if not gemini_key:
            raise RuntimeError("GEMINI_API_KEY is required. Add it to your .env file.")
        if not groq_key:
            raise RuntimeError("GROQ_API_KEY is required. Add it to your .env file.")

        self.embedding_client = genai.Client(api_key=gemini_key)
        self.llm_client = Groq(api_key=groq_key)

        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        if qdrant_url:
            self.vector_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            storage_path = os.getenv("QDRANT_LOCAL_PATH", "./data/qdrant")
            Path(storage_path).parent.mkdir(parents=True, exist_ok=True)
            self.vector_client = QdrantClient(path=storage_path)

        self._ensure_collection()

    def _ensure_collection(self) -> None:
        if not self.vector_client.collection_exists(self.collection_name):
            self.vector_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=EMBEDDING_DIMENSION,
                    distance=models.Distance.COSINE,
                ),
            )

    def _embed(self, text: str, task_type: str) -> list[float]:
        result = self.embedding_client.models.embed_content(
            model=self.embedding_model,
            contents=text,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=EMBEDDING_DIMENSION,
            ),
        )
        if not result.embeddings or not result.embeddings[0].values:
            raise RuntimeError("Gemini returned an empty embedding.")
        return list(result.embeddings[0].values)

    def _load_faqs(self) -> list[dict[str, str]]:
        if not self.faq_file_path.exists():
            raise FileNotFoundError(f"FAQ knowledge file not found: {self.faq_file_path}")
        with self.faq_file_path.open("r", encoding="utf-8") as file:
            data: Any = json.load(file)
        if not isinstance(data, list) or not data:
            raise ValueError("faqs.json must contain a non-empty JSON array.")
        faqs: list[dict[str, str]] = []
        for index, item in enumerate(data):
            if not isinstance(item, dict):
                raise ValueError(f"FAQ at index {index} must be a JSON object.")
            question = str(item.get("question", "")).strip()
            answer = str(item.get("answer", "")).strip()
            if not question or not answer:
                raise ValueError(f"FAQ at index {index} needs a question and answer.")
            faqs.append({"question": question, "answer": answer})
        return faqs

    def _clear_collection(self) -> None:
        """Remove old indexed points before rebuilding from the source FAQ file."""
        offset = None
        while True:
            points, offset = self.vector_client.scroll(
                collection_name=self.collection_name,
                limit=256,
                offset=offset,
                with_payload=False,
                with_vectors=False,
            )
            if points:
                self.vector_client.delete(
                    collection_name=self.collection_name,
                    points_selector=models.PointIdsList(points=[point.id for point in points]),
                    wait=True,
                )
            if offset is None:
                break

    def index_knowledge_base(self) -> int:
        """Embed and index every FAQ. Called once during application startup."""
        faqs = self._load_faqs()
        self._clear_collection()
        points = []
        for faq in faqs:
            searchable_text = f"Question: {faq['question']}\nAnswer: {faq['answer']}"
            vector = self._embed(searchable_text, "RETRIEVAL_DOCUMENT")
            point_id = str(uuid.uuid5(POINT_NAMESPACE, faq["question"].casefold()))
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "question": faq["question"],
                        "answer": faq["answer"],
                        "source": "faqs.json",
                    },
                )
            )
        self.vector_client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
        )
        logger.info("Indexed %s FAQ entries into %s", len(points), self.collection_name)
        return len(points)

    def retrieve(self, question: str) -> list[dict[str, Any]]:
        query_vector = self._embed(question, "RETRIEVAL_QUERY")
        hits = self.vector_client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=self.top_k,
            with_payload=True,
            score_threshold=self.score_threshold,
        )
        return [
            {
                "question": hit.payload.get("question", ""),
                "answer": hit.payload.get("answer", ""),
                "source": hit.payload.get("source", "Knowledge base"),
                "score": round(float(hit.score), 4),
            }
            for hit in hits
            if hit.payload
        ]

    def answer(self, question: str) -> dict[str, Any]:
        """Retrieve relevant FAQ entries and ask the LLM to answer from that context."""
        matches = self.retrieve(question)
        if not matches:
            message = "I couldn't find relevant information in the Cloudify knowledge base. Please contact Cloudify support for help."
            return {"reply": message, "sources": [], "retrieval_count": 0}

        context_parts = []
        for index, item in enumerate(matches, start=1):
            context_parts.append(
                f"[{index}] FAQ question: {item['question']}\n"
                f"FAQ answer: {item['answer']}\n"
                f"Source: {item['source']}"
            )
        context = "\n\n".join(context_parts)

        completion = self.llm_client.chat.completions.create(
            model=self.llm_model,
            temperature=0.2,
            max_tokens=700,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Cloudify's FAQ support assistant. Answer the user's question "
                        "using only the retrieved knowledge-base context. Do not invent policies, "
                        "prices, features, or facts. If the context does not contain the answer, "
                        "say that the knowledge base does not provide enough information and "
                        "recommend contacting support. Be clear and concise. Cite supporting "
                        "context entries inline using their bracket labels, for example [1]."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Retrieved knowledge-base context:\n{context}\n\n"
                        f"User question: {question}\n\n"
                        "Write an answer grounded in the context above."
                    ),
                },
            ],
        )
        answer_text = completion.choices[0].message.content or ""
        if not answer_text.strip():
            raise RuntimeError("The language model returned an empty response.")

        sources = [
            {
                "id": index,
                "question": item["question"],
                "source": item["source"],
                "score": item["score"],
            }
            for index, item in enumerate(matches, start=1)
        ]
        return {
            "reply": answer_text.strip(),
            "sources": sources,
            "retrieval_count": len(matches),
        }
