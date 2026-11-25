"""Initial users, conversations, messages, and FAQ citations."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    uid = sa.Uuid()
    op.create_table("users", sa.Column("id", uid, primary_key=True), sa.Column("email", sa.String(255), nullable=False), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("conversations", sa.Column("id", uid, primary_key=True), sa.Column("user_id", uid, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("title", sa.String(255), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])
    op.create_table("messages", sa.Column("id", uid, primary_key=True), sa.Column("conversation_id", uid, sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False), sa.Column("role", sa.String(20), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.CheckConstraint("role IN ('user','assistant','system')", name="ck_message_role"))
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_table("message_citations", sa.Column("id", uid, primary_key=True), sa.Column("message_id", uid, sa.ForeignKey("messages.id", ondelete="CASCADE"), nullable=False), sa.Column("faq_id", sa.String(64), nullable=False), sa.Column("question", sa.Text(), nullable=False), sa.Column("similarity", sa.Float(), nullable=False))
    op.create_index("ix_message_citations_message_id", "message_citations", ["message_id"])


def downgrade():
    op.drop_table("message_citations")
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_table("messages")
    op.drop_index("ix_conversations_user_id", table_name="conversations")
    op.drop_table("conversations")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
