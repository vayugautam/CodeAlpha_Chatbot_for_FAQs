from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models import Conversation, User
from app.schemas import ConversationCreate, ConversationDetail, ConversationResponse
from app.services.conversation_service import delete_conversation, get_owned_conversation, list_conversations

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationResponse, status_code=201)
def create(payload: ConversationCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    record = Conversation(user_id=user.id, title=payload.title.strip() or "New conversation")
    db.add(record); db.commit(); db.refresh(record)
    return record


@router.get("", response_model=list[ConversationResponse])
def list_items(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list_conversations(db, user)


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_item(conversation_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_owned_conversation(db, conversation_id, user)


@router.delete("/{conversation_id}", status_code=204)
def delete_item(conversation_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    delete_conversation(db, conversation_id, user)
    return Response(status_code=204)
