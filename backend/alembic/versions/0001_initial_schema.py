"""0001_initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-30 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 0. Vector Extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 1. Users Table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 2. Products Table
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('stock', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint('stock >= 0', name='chk_products_stock_non_negative'),
        sa.CheckConstraint('price >= 0', name='chk_products_price_non_negative'),
    )
    op.create_index('ix_products_id', 'products', ['id'])
    op.create_index('idx_products_title', 'products', ['title'])
    op.create_index('idx_products_price', 'products', ['price'])

    # 3. Orders Table
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint('total_amount >= 0', name='chk_orders_total_amount_non_negative'),
        sa.CheckConstraint("status IN ('PENDING', 'PAID', 'FAILED', 'CANCELLED')", name='chk_orders_status_valid'),
    )
    op.create_index('ix_orders_id', 'orders', ['id'])
    op.create_index('idx_orders_status', 'orders', ['status'])
    op.create_index('idx_orders_user_id_created_at', 'orders', ['user_id', 'created_at'])

    # 4. Order Items Table
    op.create_table(
        'order_items',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.CheckConstraint('quantity > 0', name='chk_order_items_quantity_positive'),
        sa.CheckConstraint('unit_price >= 0', name='chk_order_items_unit_price_non_negative'),
    )
    op.create_index('ix_order_items_id', 'order_items', ['id'])
    op.create_index('ix_order_items_order_id', 'order_items', ['order_id'])
    op.create_index('ix_order_items_product_id', 'order_items', ['product_id'])

    # 5. Idempotency Keys Table
    op.create_table(
        'idempotency_keys',
        sa.Column('idempotency_key', sa.String(length=128), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('request_hash', sa.String(length=64), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    op.create_index('ix_idempotency_keys_user_id', 'idempotency_keys', ['user_id'])

    # 6. Projects Table
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    op.create_index('ix_projects_id', 'projects', ['id'])
    op.create_index('ix_projects_user_id', 'projects', ['user_id'])

    # 7. Episodes Table
    op.create_table(
        'episodes',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('audio_url', sa.String(length=512), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('mime_type', sa.String(length=64), nullable=False),
        sa.Column('duration', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('language', sa.String(length=16), nullable=True, server_default='en'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='uploaded'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_episodes_id', 'episodes', ['id'])
    op.create_index('ix_episodes_project_id', 'episodes', ['project_id'])
    op.create_index('ix_episodes_status', 'episodes', ['status'])

    # 8. Speakers Table
    op.create_table(
        'speakers',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('episode_id', sa.Integer(), sa.ForeignKey('episodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('label', sa.String(length=64), nullable=False),
        sa.Column('display_name', sa.String(length=128), nullable=False),
        sa.Column('speaking_duration', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('segment_count', sa.Integer(), nullable=False, server_default='0'),
    )
    op.create_index('ix_speakers_id', 'speakers', ['id'])
    op.create_index('ix_speakers_episode_id', 'speakers', ['episode_id'])

    # 9. Transcript Segments Table
    op.create_table(
        'transcript_segments',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('episode_id', sa.Integer(), sa.ForeignKey('episodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('speaker_id', sa.Integer(), sa.ForeignKey('speakers.id', ondelete='SET NULL'), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('start_time', sa.Float(), nullable=False),
        sa.Column('end_time', sa.Float(), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
    )
    op.create_index('ix_transcript_segments_id', 'transcript_segments', ['id'])
    op.create_index('ix_transcript_segments_episode_id', 'transcript_segments', ['episode_id'])
    op.create_index('ix_transcript_segments_speaker_id', 'transcript_segments', ['speaker_id'])
    op.create_index('ix_transcript_segments_start_time', 'transcript_segments', ['start_time'])
    op.create_index('ix_transcript_segments_sequence_number', 'transcript_segments', ['sequence_number'])
    op.create_index('idx_segment_episode_seq', 'transcript_segments', ['episode_id', 'sequence_number'])

    # 10. Chunk Embeddings Table (pgvector)
    op.create_table(
        'chunk_embeddings',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('episode_id', sa.Integer(), sa.ForeignKey('episodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('segment_id', sa.Integer(), sa.ForeignKey('transcript_segments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('speaker_label', sa.Text(), nullable=True),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('start_time', sa.Float(), nullable=False),
        sa.Column('end_time', sa.Float(), nullable=False),
        sa.Column('embedding', Vector(768), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    op.create_index('ix_chunk_embeddings_id', 'chunk_embeddings', ['id'])
    op.create_index('ix_chunk_embeddings_episode_id', 'chunk_embeddings', ['episode_id'])
    op.create_index('ix_chunk_embeddings_start_time', 'chunk_embeddings', ['start_time'])

    # 11. Processing Jobs Table
    op.create_table(
        'processing_jobs',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('episode_id', sa.Integer(), sa.ForeignKey('episodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='queued'),
        sa.Column('current_stage', sa.String(length=64), nullable=False, server_default='upload'),
        sa.Column('progress', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_processing_jobs_id', 'processing_jobs', ['id'])
    op.create_index('ix_processing_jobs_episode_id', 'processing_jobs', ['episode_id'])

    # 12. Saved Searches Table
    op.create_table(
        'saved_searches',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('filters', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    op.create_index('ix_saved_searches_id', 'saved_searches', ['id'])
    op.create_index('ix_saved_searches_user_id', 'saved_searches', ['user_id'])
    op.create_index('ix_saved_searches_project_id', 'saved_searches', ['project_id'])

    # 13. Notifications Table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('type', sa.String(length=64), nullable=False, server_default='info'),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    op.create_index('ix_notifications_id', 'notifications', ['id'])
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_is_read', 'notifications', ['is_read'])

    # 14. Episode Insights Table
    op.create_table(
        'episode_insights',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('episode_id', sa.Integer(), sa.ForeignKey('episodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('overview', sa.Text(), nullable=False),
        sa.Column('target_competencies', sa.JSON(), nullable=False),
        sa.Column('core_tech_stack', sa.JSON(), nullable=False),
        sa.Column('architectural_blueprint', sa.JSON(), nullable=False),
        sa.Column('resume_transformation', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    op.create_index('ix_episode_insights_id', 'episode_insights', ['id'])
    op.create_index('ix_episode_insights_episode_id', 'episode_insights', ['episode_id'], unique=True)


def downgrade() -> None:
    op.drop_table('episode_insights')
    op.drop_table('notifications')
    op.drop_table('saved_searches')
    op.drop_table('processing_jobs')
    op.drop_table('chunk_embeddings')
    op.drop_table('transcript_segments')
    op.drop_table('speakers')
    op.drop_table('episodes')
    op.drop_table('projects')
    op.drop_table('idempotency_keys')
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('products')
    op.drop_table('users')
    op.execute("DROP EXTENSION IF EXISTS vector;")
