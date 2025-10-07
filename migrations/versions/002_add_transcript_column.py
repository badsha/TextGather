"""Add transcript column to submissions table

Revision ID: 002_add_transcript
Revises: 001_initial_schema
Create Date: 2025-10-06 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_transcript'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    # Check if transcript column exists before adding
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'submissions' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('submissions')]
        if 'transcript' not in columns:
            with op.batch_alter_table('submissions', schema=None) as batch_op:
                batch_op.add_column(sa.Column('transcript', sa.Text(), nullable=True))
            print("✓ Added transcript column to submissions table")
        else:
            print("ℹ Transcript column already exists, skipping")


def downgrade():
    # Remove transcript column
    with op.batch_alter_table('submissions', schema=None) as batch_op:
        batch_op.drop_column('transcript')
