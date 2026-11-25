from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models import Message, MessageCitation, User
from app.schemas import ChatRequest, ChatResponse
from app.services.conversation_service import get_owned_conversation
from app.services.llm_service import generate_answer
from app.services.retrieval_service import retrieve

router = APIRouter(prefix="/conversations", tags=["chat"])


@router.post("/{conversation_id}/chat", response_model=ChatResponse)
def chat(conversation_id: UUID, payload: ChatRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    conversation = get_owned_conversation(db, conversation_id, user)
    question = payload.message
    try:
        records = retrieve(question)
        result = generate_answer(question, records)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="FAQ answer service is temporarily unavailable") from exc
    user_message = Message(conversation_id=conversation.id, role="user", content=question)
    db.add(user_message); db.flush()
    assistant = Message(conversation_id=conversation.id, role="assistant", content=result["answer"])
    db.add(assistant); db.flush()
    for source in result["sources"]:
        db.add(MessageCitation(message_id=assistant.id, faq_id=source["faq_id"], question=source["question"], similarity=source["similarity"]))
    if conversation.title == "New conversation":
        conversation.title = question[:70]
    db.commit()
    return ChatResponse(answer=result["answer"], sources=result["sources"], conversation_id=conversation.id)
