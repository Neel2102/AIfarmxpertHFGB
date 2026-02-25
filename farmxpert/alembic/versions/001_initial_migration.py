"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create farms table
    op.create_table('farms',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=False),
        sa.Column('size_acres', sa.Float(), nullable=False),
        sa.Column('farmer_name', sa.String(length=255), nullable=False),
        sa.Column('farmer_phone', sa.String(length=20), nullable=True),
        sa.Column('farmer_email', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create fields table
    op.create_table('fields',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('farm_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('size_acres', sa.Float(), nullable=False),
        sa.Column('soil_type', sa.String(length=100), nullable=True),
        sa.Column('irrigation_type', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create crops table
    op.create_table('crops',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('farm_id', sa.Integer(), nullable=False),
        sa.Column('field_id', sa.Integer(), nullable=True),
        sa.Column('crop_type', sa.String(length=100), nullable=False),
        sa.Column('variety', sa.String(length=100), nullable=True),
        sa.Column('planting_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expected_harvest_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('area_acres', sa.Float(), nullable=False),
        sa.Column('seed_quantity', sa.Float(), nullable=True),
        sa.Column('seed_cost', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ),
        sa.ForeignKeyConstraint(['field_id'], ['fields.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create tasks table
    op.create_table('tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('farm_id', sa.Integer(), nullable=False),
        sa.Column('crop_id', sa.Integer(), nullable=True),
        sa.Column('task_type', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('scheduled_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('priority', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('assigned_to', sa.String(length=255), nullable=True),
        sa.Column('cost', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['crop_id'], ['crops.id'], ),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('tasks')
    op.drop_table('crops')
    op.drop_table('fields')
    op.drop_table('farms')
