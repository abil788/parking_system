"""add performance indexes

Revision ID: 1da0ce18a994
Revises: 732b65457787
Create Date: 2025-10-04 16:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1da0ce18a994'
down_revision = '732b65457787'
branch_labels = None
depends_on = None


def upgrade():
    # Composite index for log queries
    op.create_index(
        'ix_access_logs_timestamp_result',
        'access_logs',
        ['timestamp', 'result']
    )
    
    op.create_index(
        'ix_access_logs_card_timestamp',
        'access_logs',
        ['card_id', 'timestamp']
    )
    
    op.create_index(
        'ix_access_logs_reader_timestamp',
        'access_logs',
        ['reader_id', 'timestamp']
    )
    
    # Index for card status queries
    op.create_index(
        'ix_cards_status',
        'cards',
        ['status']
    )


def downgrade():
    op.drop_index('ix_access_logs_timestamp_result', table_name='access_logs')
    op.drop_index('ix_access_logs_card_timestamp', table_name='access_logs')
    op.drop_index('ix_access_logs_reader_timestamp', table_name='access_logs')
    op.drop_index('ix_cards_status', table_name='cards')