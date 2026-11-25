"""FAQ dataset validation and idempotent Qdrant synchronization."""
import hashlib
import json
import uuid
from pathlib import Path

from qdrant_client import models

from app.services.embedding_service import DIMENSIONS, generate_embedding
from app.services.qdrant_service import COLLECTION_NAME, ensure_collection, get_qdrant_client

FAQ_PATH = Path(__file__).resolve().parents[2] / "faqs.json"
ID_NAMESPACE = uuid.UUID("18d09177-849c-4a5a-a64c-21bafc4bbfe9")


def load_faqs(path: Path = FAQ_PATH) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("faqs.json must contain a non-empty array")
    records, ids = [], set()
    for index, item in enumerate(data):
        if not isinstance(item, dict) or not isinstance(item.get("question"), str) or not isinstance(item.get("answer"), str):
            raise ValueError(f"FAQ entry {index} must contain question and answer strings")
        question, answer = item["question"].strip(), item["answer"].strip()
        if not question or not answer:
            raise ValueError(f"FAQ entry {index} has an empty question or answer")
        faq_id = str(uuid.uuid5(ID_NAMESPACE, question.casefold()))
        if faq_id in ids:
            raise ValueError(f"Duplicate FAQ question: {question}")
        ids.add(faq_id)
        record = {"faq_id": faq_id, "question": question, "answer": answer, "source_file": path.name}
        if isinstance(item.get("category"), str):
            record["category"] = item["category"].strip()
        records.append(record)
    return records


def sync_faqs(path: Path = FAQ_PATH) -> int:
    records = load_faqs(path)
    client = get_qdrant_client()
    ensure_collection(client)
    points = []
    for record in records:
        text = f"Question: {record['question']}\nAnswer: {record['answer']}"
        vector = generate_embedding(text)
        if len(vector) != DIMENSIONS:
            raise ValueError("FAQ embedding dimensions do not match the Qdrant collection")
        points.append(models.PointStruct(id=record["faq_id"], vector=vector, payload={**record, "content_hash": hashlib.sha256(text.encode()).hexdigest()}))
    if points:
        client.upsert(collection_name=COLLECTION_NAME, points=points, wait=True)
    keep = {record["faq_id"] for record in records}
    stale, offset = [], None
    while True:
        batch, offset = client.scroll(collection_name=COLLECTION_NAME, limit=256, offset=offset, with_payload=["faq_id"], with_vectors=False)
        stale.extend(str(point.id) for point in batch if str(point.payload.get("faq_id", point.id)) not in keep)
        if offset is None:
            break
    if stale:
        client.delete(collection_name=COLLECTION_NAME, points_selector=models.PointIdsList(points=stale), wait=True)
    return len(records)
