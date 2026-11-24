"""FastAPI application for the Cloudify Retrieval-Augmented FAQ chatbot."""
import asyncio
import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from rag_service import FAQRAGService

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)
rag_service: FAQRAGService | None = None
indexed_faq_count = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag_service, indexed_faq_count
    service = FAQRAGService()
    indexed_faq_count = await asyncio.to_thread(service.index_knowledge_base)
    rag_service = service
    logger.info("RAG chatbot is ready with %s indexed FAQs.", indexed_faq_count)
    yield
    rag_service = None


app = FastAPI(
    title="Cloudify RAG FAQ Chatbot",
    description="A Retrieval-Augmented Generation chatbot powered by Gemini, Qdrant, and Groq.",
    version="2.0.0",
    lifespan=lifespan,
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class Source(BaseModel):
    id: int
    question: str
    source: str
    score: float


class ChatResponse(BaseModel):
    reply: str
    sources: list[Source]
    retrieval_count: int


@app.get("/health")
async def health():
    return {
        "status": "ok" if rag_service is not None else "starting",
        "service": "cloudify-rag-chatbot",
        "indexed_faqs": indexed_faq_count,
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if rag_service is None:
        raise HTTPException(status_code=503, detail="The RAG knowledge base is not ready.")
    try:
        result = rag_service.answer(request.message.strip())
        return ChatResponse(**result)
    except Exception as exc:
        logger.exception("RAG request failed")
        raise HTTPException(
            status_code=502,
            detail="The chatbot could not complete the request. Check the server logs and API configuration.",
        ) from exc


os.makedirs("static", exist_ok=True)
app.mount("/", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=True)
