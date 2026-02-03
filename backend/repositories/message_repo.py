from sqlalchemy.orm import Session
from models.message import Message
from models.conversations import Conversation


def fetch_history(
    db: Session,
    *,
    conversation_id: int,
    user_id: int
):
    return (
        db.query(Message)
        .join(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        )
        .order_by(Message.created_at.asc())
        .all()
    )


def save_messages(
    db: Session,
    *,
    conversation_id: int,
    user_message: str,
    assistant_message: str
):
    db.add_all([
        Message(
            conversation_id=conversation_id,
            role="user",
            message=user_message
        ),
        Message(
            conversation_id=conversation_id,
            role="assistant",
            message=assistant_message
        )
    ])


def delete_messages(
    db: Session,
    *,
    conversation_id: int
):
    db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).delete(synchronize_session=False)