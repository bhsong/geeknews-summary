"""initial schema snapshot (PHP migrations 001~003)

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

TABLE_OPTS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}

NOW = sa.text("CURRENT_TIMESTAMP")
NOW_ON_UPDATE = sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.create_table(
        "summaries",
        sa.Column(
            "topic_id",
            mysql.INTEGER(unsigned=True),
            primary_key=True,
            autoincrement=False,
        ),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("title", sa.String(500), nullable=False, server_default=""),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("model", sa.String(50), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=NOW),
        sa.Column(
            "updated_at", sa.DateTime, nullable=False, server_default=NOW_ON_UPDATE
        ),
        **TABLE_OPTS,
    )

    op.create_table(
        "articles",
        sa.Column(
            "topic_id",
            mysql.INTEGER(unsigned=True),
            primary_key=True,
            autoincrement=False,
        ),
        sa.Column("title", sa.String(500), nullable=False, server_default=""),
        sa.Column("content", mysql.MEDIUMTEXT, nullable=False),
        sa.Column("crawled_at", sa.DateTime, nullable=False, server_default=NOW),
        **TABLE_OPTS,
    )
    op.create_index(
        "ft_content",
        "articles",
        ["title", "content"],
        mysql_prefix="FULLTEXT",
        mysql_with_parser="ngram",
    )

    op.create_table(
        "chat_session",
        sa.Column(
            "id", mysql.INTEGER(unsigned=True), primary_key=True, autoincrement=True
        ),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=NOW),
        **TABLE_OPTS,
    )

    op.create_table(
        "chat_message",
        sa.Column(
            "id", mysql.INTEGER(unsigned=True), primary_key=True, autoincrement=True
        ),
        sa.Column("session_id", mysql.INTEGER(unsigned=True), nullable=False),
        sa.Column("role", mysql.ENUM("user", "model"), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=NOW),
        **TABLE_OPTS,
    )
    op.create_index("idx_session", "chat_message", ["session_id"])
    # idx_session을 먼저 만들어야 InnoDB가 FK용 인덱스 중복 생성하지 않음
    op.create_foreign_key(
        "fk_messages_session",
        "chat_message",
        "chat_session",
        ["session_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_table("chat_message")
    op.drop_table("chat_session")
    op.drop_table("articles")
    op.drop_table("summaries")
