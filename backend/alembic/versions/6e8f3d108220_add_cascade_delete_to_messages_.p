"""add cascade delete to messages.conversation_id

Revision ID: 6e8f3d108220
Revises: 
Create Date: 2026-01-12 01:44:31.327093

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e8f3d108220'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Drop existing foreign key constraint
    op.drop_constraint(
        "messages_conversation_id_fkey",
        "messages",
        type_="foreignkey"
    )

    # Re-create foreign key with ON DELETE CASCADE
    op.create_foreign_key(
        "messages_conversation_id_fkey",
        "messages",
        "conversations",
        ["conversation_id"],
        ["id"],
        ondelete="CASCADE"
    )
def downgrade():
    # Drop cascade foreign key
    op.drop_constraint(
        "messages_conversation_id_fkey",
        "messages",
        type_="foreignkey"
    )

    # Re-create original foreign key (no cascade)
    op.create_foreign_key(
        "messages_conversation_id_fkey",
        "messages",
        "conversations",
        ["conversation_id"],
        ["id"]
    )

