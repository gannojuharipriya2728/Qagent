"""add faculty_id to courses

Revision ID: 7a8b9c0d1e2f
Revises: 55d4e7f3e1f4
Create Date: 2026-09-22 13:48:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = '7a8b9c0d1e2f'
down_revision: Union[str, Sequence[str], None] = '55d4e7f3e1f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    existing_tables = inspector.get_table_names()

    if "courses" in existing_tables:
        course_cols = [col["name"] for col in inspector.get_columns("courses")]
        with op.batch_alter_table("courses", schema=None) as batch_op:
            if "faculty_id" not in course_cols:
                batch_op.add_column(sa.Column("faculty_id", sa.Integer(), nullable=True))
                # Add index on faculty_id
                batch_op.create_index("ix_courses_faculty_id", ["faculty_id"], unique=False)
                # Add foreign key constraint if users table exists
                if "users" in existing_tables:
                    batch_op.create_foreign_key(
                        "fk_courses_users_faculty_id",
                        "users",
                        ["faculty_id"],
                        ["id"],
                        ondelete="SET NULL"
                    )
            if "analysis_status" not in course_cols:
                batch_op.add_column(sa.Column("analysis_status", sa.String(50), server_default="Pending", nullable=True))
            if "analysis_data" not in course_cols:
                batch_op.add_column(sa.Column("analysis_data", sa.JSON(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    existing_tables = inspector.get_table_names()

    if "courses" in existing_tables:
        course_cols = [col["name"] for col in inspector.get_columns("courses")]
        with op.batch_alter_table("courses", schema=None) as batch_op:
            if "faculty_id" in course_cols:
                try:
                    batch_op.drop_constraint("fk_courses_users_faculty_id", type_="foreignkey")
                except Exception:
                    pass
                try:
                    batch_op.drop_index("ix_courses_faculty_id")
                except Exception:
                    pass
                batch_op.drop_column("faculty_id")
            if "analysis_status" in course_cols:
                batch_op.drop_column("analysis_status")
            if "analysis_data" in course_cols:
                batch_op.drop_column("analysis_data")
