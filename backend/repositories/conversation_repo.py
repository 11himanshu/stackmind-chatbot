from sqlalchemy.orm import Session
from models.conversations import Conversation


def get_conversation(
    db: Session,
    *,
    conversation_id: int,
    user_id: int
):
    return (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        )
        .first()
    )


def create_conversation(
    db: Session,
    *,
    user_id: int
) -> Conversation:
    conversation = Conversation(user_id=user_id)
    db.add(conversation)
    db.flush()
    return conversation


def list_conversations(
    db: Session,
    *,
    user_id: int
):
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.id.desc())
        .all()
    )


def delete_conversation(
    db: Session,
    *,
    conversation_id: int,
    user_id: int
) -> bool:
    conversation = get_conversation(
        db,
        conversation_id=conversation_id,
        user_id=user_id
    )

    if not conversation:
        return False

    db.delete(conversation)
    return True