"""Initial schema - base tables already created by db.create_all()

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-10-06 20:00:00.000000

This is the base migration that assumes tables are already created by SQLAlchemy's db.create_all().
We stamp this migration as complete on first run, then future migrations build on top of it.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # This migration does nothing - it's just a marker
    # The actual schema is created by db.create_all() in the entrypoint
    # We use 'flask db stamp head' to mark this as complete
    pass


def downgrade():
    # No downgrade needed for base schema
    pass
