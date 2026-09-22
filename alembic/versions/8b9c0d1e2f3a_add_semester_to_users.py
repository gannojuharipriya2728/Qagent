"""add semester to users

Revision ID: 8b9c0d1e2f3a
Revises: 7a8b9c0d1e2f
Create Date: 2026-09-22 15:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = '8b9c0d1e2f3a'
down_revision: Union[str, Sequence[str], None] = '7a8b9c0d1e2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    existing_tables = inspector.get_table_names()

    if "users" in existing_tables:
        user_cols = [col["name"] for col in inspector.get_columns("users")]
        with op.batch_alter_table("users", schema=None) as batch_op:
            if "semester" not in user_cols:
                batch_op.add_column(sa.Column("semester", sa.String(50), server_default="Semester V", nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    existing_tables = inspector.get_table_names()

    if "users" in existing_tables:
        user_cols = [col["name"] for col in inspector.get_columns("users")]
        with op.batch_alter_table("users", schema=None) as batch_op:
            if "semester" in user_cols:
                batch_op.drop_column("semester")
