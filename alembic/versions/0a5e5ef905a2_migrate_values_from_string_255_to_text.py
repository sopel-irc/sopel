"""migrate values from string(255) to text

Revision ID: 0a5e5ef905a2
Revises: 
Create Date: 2022-06-01 20:37:23.690802

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0a5e5ef905a2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('channel_values') as bop:
        bop.alter_column(
            column_name='value',
            type_=sa.Text,
            existing_type=sa.String(255),
            existing_nullable=True,
            existing_server_default=sa.String(255),
        )

    with op.batch_alter_table('nick_values') as bop:
        bop.alter_column(
            column_name='value',
            type_=sa.Text,
            existing_type=sa.String(255),
            existing_nullable=True,
            existing_server_default=sa.String(255),
        )


def downgrade() -> None:
    with op.batch_alter_table('channel_values') as bop:
        bop.alter_column(
            column_name='value',
            type_=sa.String(255),
            existing_type=sa.Text,
            existing_nullable=True,
            existing_server_default=sa.Text,
        )
