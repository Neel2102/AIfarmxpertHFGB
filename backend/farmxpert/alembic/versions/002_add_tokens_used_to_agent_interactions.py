from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agent_interactions", sa.Column("tokens_used", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("agent_interactions", "tokens_used")
