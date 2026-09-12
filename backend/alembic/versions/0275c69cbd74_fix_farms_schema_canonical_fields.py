"""Ensure farms table has canonical farm_name and all required columns

Revision ID: 0275c69cbd74
Revises: 0275c69cbd73
Create Date: 2026-03-12 18:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = '0275c69cbd74'
down_revision: Union[str, None] = '0275c69cbd73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('farms')] if 'farms' in inspector.get_table_names() else []

    # If table exists, ensure all canonical columns are present
    if 'farms' in inspector.get_table_names():
        # Ensure farm_name exists
        if 'farm_name' not in existing_columns:
            op.add_column('farms', sa.Column('farm_name', sa.String(length=255), nullable=True))
            # If legacy 'name' column exists, migrate values over
            if 'name' in existing_columns:
                op.execute("UPDATE farms SET farm_name = name WHERE farm_name IS NULL")
            op.execute("UPDATE farms SET farm_name = 'My Farm' WHERE farm_name IS NULL")
            op.alter_column('farms', 'farm_name', nullable=False)

        # Ensure location exists
        if 'location' not in existing_columns:
            op.add_column('farms', sa.Column('location', sa.String(length=255), nullable=True))

        # Ensure size_acres exists
        if 'size_acres' not in existing_columns:
            op.add_column('farms', sa.Column('size_acres', sa.Float(), nullable=True, server_default='5.0'))

        # Ensure farmer contact info exists
        if 'farmer_name' not in existing_columns:
            op.add_column('farms', sa.Column('farmer_name', sa.String(length=255), nullable=True))
        if 'farmer_phone' not in existing_columns:
            op.add_column('farms', sa.Column('farmer_phone', sa.String(length=50), nullable=True))
        if 'farmer_email' not in existing_columns:
            op.add_column('farms', sa.Column('farmer_email', sa.String(length=255), nullable=True))

        # Ensure agronomy / geographic columns exist
        if 'crop_type' not in existing_columns:
            op.add_column('farms', sa.Column('crop_type', sa.String(length=100), nullable=True))
        if 'state' not in existing_columns:
            op.add_column('farms', sa.Column('state', sa.String(length=100), nullable=True))
        if 'district' not in existing_columns:
            op.add_column('farms', sa.Column('district', sa.String(length=100), nullable=True))
        if 'village' not in existing_columns:
            op.add_column('farms', sa.Column('village', sa.String(length=100), nullable=True))
        if 'latitude' not in existing_columns:
            op.add_column('farms', sa.Column('latitude', sa.Numeric(10, 7), nullable=True))
        if 'longitude' not in existing_columns:
            op.add_column('farms', sa.Column('longitude', sa.Numeric(10, 7), nullable=True))
        if 'soil_type' not in existing_columns:
            op.add_column('farms', sa.Column('soil_type', sa.String(length=100), nullable=True))


def downgrade() -> None:
    pass
