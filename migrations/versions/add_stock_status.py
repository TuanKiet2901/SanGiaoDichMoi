"""add stock status to products

Revision ID: add_stock_status
Revises: 
Create Date: 2024-03-21

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_stock_status'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add stock_status column to products table
    op.add_column('products', sa.Column('stock_status', sa.String(20), nullable=False, server_default='in_stock'))

def downgrade():
    # Remove stock_status column from products table
    op.drop_column('products', 'stock_status') 