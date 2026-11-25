"""Database operations for conversations and chat turns."""
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Conversation, Message, MessageCitation, User


def get_owned_conversation(db: Session, conversation_id: UUID, user: User) -> Conversation:
    conversation = db.scalar(select(Conversation).options(selectinload(Conversation.messages).selectinload(Message.citations)).where(Conversation.id == conversation_id, Conversation.user_id == user.id))
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


def list_conversations(db: Session, user: User):
    return list(db.scalars(select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.updated_at.desc())))


def delete_conversation(db: Session, conversation_id: UUID, user: User) -> None:
    conversation = db.scalar(select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id))
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conversation)
    db.commit()
