"""initial_qagent_schema

Revision ID: 55d4e7f3e1f4
Revises: 
Create Date: 2026-09-20 22:27:07.053836

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision: str = '55d4e7f3e1f4'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    existing_tables = inspector.get_table_names()

    # 1. users table
    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("email", sa.String(255), unique=True, index=True, nullable=False),
            sa.Column("full_name", sa.String(255), nullable=False),
            sa.Column("hashed_password", sa.String(255), nullable=False),
            sa.Column("role", sa.String(50), default="faculty", nullable=False),
            sa.Column("department", sa.String(100), default="Computer Science & Engineering"),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )

    # 2. courses table
    if "courses" not in existing_tables:
        op.create_table(
            "courses",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("code", sa.String(50), unique=True, index=True, nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("department", sa.String(100), default="Computer Science & Engineering"),
            sa.Column("semester", sa.String(50), default="Semester V"),
            sa.Column("academic_year", sa.String(50), default="2025-2026"),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )

    # 3. units table
    if "units" not in existing_tables:
        op.create_table(
            "units",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id"), nullable=False),
            sa.Column("unit_number", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("topics", sa.Text(), nullable=False),
        )

    # 4. course_outcomes table
    if "course_outcomes" not in existing_tables:
        op.create_table(
            "course_outcomes",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id"), nullable=False),
            sa.Column("code", sa.String(20), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("target_bloom_level", sa.String(50), default="Apply"),
        )

    # 5. resources table
    if "resources" not in existing_tables:
        op.create_table(
            "resources",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id"), nullable=False),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("file_name", sa.String(255), nullable=False),
            sa.Column("file_path", sa.String(500), nullable=False),
            sa.Column("storage_key", sa.String(500), nullable=True),
            sa.Column("file_type", sa.String(50), nullable=False),
            sa.Column("document_type", sa.String(50), nullable=False),
            sa.Column("unit_number", sa.Integer(), nullable=True),
            sa.Column("file_size_bytes", sa.Integer(), default=0),
            sa.Column("status", sa.String(50), default="Uploaded"),
            sa.Column("chunk_count", sa.Integer(), default=0),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("uploaded_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
    else:
        # If resources already exists, ensure storage_key column exists
        resource_columns = [col["name"] for col in inspector.get_columns("resources")]
        if "storage_key" not in resource_columns:
            with op.batch_alter_table("resources", schema=None) as batch_op:
                batch_op.add_column(sa.Column("storage_key", sa.String(length=500), nullable=True))

    # 6. resource_chunks table
    if "resource_chunks" not in existing_tables:
        op.create_table(
            "resource_chunks",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("resource_id", sa.Integer(), sa.ForeignKey("resources.id"), nullable=False),
            sa.Column("chunk_index", sa.Integer(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("page_number", sa.Integer(), nullable=True),
            sa.Column("unit_number", sa.Integer(), nullable=True),
            sa.Column("topic", sa.String(255), nullable=True),
            sa.Column("token_count", sa.Integer(), default=0),
            sa.Column("embedding_id", sa.String(100), nullable=True),
        )

    # 7. question_papers table
    if "question_papers" not in existing_tables:
        op.create_table(
            "question_papers",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id"), nullable=False),
            sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("examination_name", sa.String(255), default="Semester End Examination"),
            sa.Column("institution_name", sa.String(255), default="Department of Computer Science & Engineering"),
            sa.Column("duration_minutes", sa.Integer(), default=180),
            sa.Column("total_marks", sa.Integer(), nullable=False),
            sa.Column("section_config", sa.JSON(), nullable=True),
            sa.Column("instructions", sa.Text(), nullable=True),
            sa.Column("difficulty_distribution", sa.JSON(), nullable=True),
            sa.Column("bloom_distribution", sa.JSON(), nullable=True),
            sa.Column("syllabus_coverage_score", sa.Float(), default=0.0),
            sa.Column("status", sa.String(50), default="Generated"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )

    # 8. questions table
    if "questions" not in existing_tables:
        op.create_table(
            "questions",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("paper_id", sa.Integer(), sa.ForeignKey("question_papers.id"), nullable=False),
            sa.Column("section_name", sa.String(50), default="Section A"),
            sa.Column("question_number", sa.Integer(), nullable=False),
            sa.Column("sub_question_letter", sa.String(10), nullable=True),
            sa.Column("question_text", sa.Text(), nullable=False),
            sa.Column("marks", sa.Integer(), nullable=False),
            sa.Column("unit_number", sa.Integer(), nullable=False),
            sa.Column("bloom_level", sa.String(50), nullable=False),
            sa.Column("course_outcome", sa.String(50), nullable=False),
            sa.Column("difficulty", sa.String(50), default="Medium"),
            sa.Column("question_type", sa.String(50), default="Descriptive"),
            sa.Column("source_topics", sa.JSON(), nullable=True),
            sa.Column("source_documents", sa.JSON(), nullable=True),
            sa.Column("generation_reasoning", sa.Text(), nullable=True),
            sa.Column("is_revised", sa.Boolean(), default=False),
            sa.Column("revision_count", sa.Integer(), default=0),
        )

    # 9. generation_sessions table
    if "generation_sessions" not in existing_tables:
        op.create_table(
            "generation_sessions",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("paper_id", sa.Integer(), sa.ForeignKey("question_papers.id"), nullable=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("status", sa.String(50), default="InProgress"),
            sa.Column("steps_log", sa.JSON(), nullable=True),
            sa.Column("duration_seconds", sa.Float(), default=0.0),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )

    # 10. validation_results table
    if "validation_results" not in existing_tables:
        op.create_table(
            "validation_results",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("question_id", sa.Integer(), sa.ForeignKey("questions.id"), nullable=False),
            sa.Column("is_valid", sa.Boolean(), default=True),
            sa.Column("syllabus_alignment_score", sa.Float(), default=1.0),
            sa.Column("co_alignment_score", sa.Float(), default=1.0),
            sa.Column("difficulty_match_score", sa.Float(), default=1.0),
            sa.Column("bloom_alignment_score", sa.Float(), default=1.0),
            sa.Column("is_duplicate", sa.Boolean(), default=False),
            sa.Column("duplicate_similarity_score", sa.Float(), default=0.0),
            sa.Column("feedback_notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )

def downgrade() -> None:
    op.drop_table("validation_results")
    op.drop_table("generation_sessions")
    op.drop_table("questions")
    op.drop_table("question_papers")
    op.drop_table("resource_chunks")
    op.drop_table("resources")
    op.drop_table("course_outcomes")
    op.drop_table("units")
    op.drop_table("courses")
    op.drop_table("users")
