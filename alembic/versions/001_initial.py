"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-12-09 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create enum types
    op.execute("CREATE TYPE urgency_level AS ENUM ('low', 'medium', 'high', 'critical')")
    op.execute("CREATE TYPE email_status AS ENUM ('new', 'processed', 'responded', 'failed')")

    # Create emails table
    op.create_table(
        'emails',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.String(), nullable=False),
        sa.Column('thread_id', sa.String(), nullable=True),
        sa.Column('sender_email', sa.String(), nullable=False),
        sa.Column('sender_name', sa.String(), nullable=True),
        sa.Column('recipient_email', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('received_at', sa.DateTime(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('main_category', sa.String(), nullable=True),
        sa.Column('sub_category', sa.String(), nullable=True),
        sa.Column('classification_confidence', sa.Float(), nullable=True),
        sa.Column('keywords', postgresql.JSONB(), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('urgency', postgresql.ENUM('low', 'medium', 'high', 'critical', name='urgency_level'), nullable=True),
        sa.Column('status', postgresql.ENUM('new', 'processed', 'responded', 'failed', name='email_status'), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('is_reply', sa.Boolean(), nullable=False),
        sa.Column('additional_data', postgresql.JSONB(), nullable=True),
        sa.Column('archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_emails_message_id', 'emails', ['message_id'], unique=True)
    op.create_index('ix_emails_thread_id', 'emails', ['thread_id'])
    op.create_index('ix_emails_sender_email', 'emails', ['sender_email'])

    # Create responses table
    op.create_table(
        'responses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('model_version', sa.String(), nullable=True),
        sa.Column('prompt_tokens', sa.Integer(), nullable=True),
        sa.Column('completion_tokens', sa.Integer(), nullable=True),
        sa.Column('total_tokens', sa.Integer(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('is_sent', sa.Boolean(), nullable=False),
        sa.Column('send_attempts', sa.Integer(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('was_helpful', sa.Boolean(), nullable=True),
        sa.Column('customer_replied', sa.Boolean(), nullable=False),
        sa.Column('is_manual', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['email_id'], ['emails.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create customers table
    op.create_table(
        'customers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('account_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('subscription_status', sa.String(), nullable=True),
        sa.Column('subscription_end_date', sa.DateTime(), nullable=True),
        sa.Column('last_contact', sa.DateTime(), nullable=True),
        sa.Column('total_tickets', sa.Integer(), nullable=False),
        sa.Column('preferences', postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_customers_email', 'customers', ['email'], unique=True)
    op.create_index('ix_customers_account_id', 'customers', ['account_id'], unique=True)

def downgrade():
    op.drop_table('responses')
    op.drop_table('emails')
    op.drop_table('customers')
    op.execute('DROP TYPE urgency_level')
    op.execute('DROP TYPE email_status')