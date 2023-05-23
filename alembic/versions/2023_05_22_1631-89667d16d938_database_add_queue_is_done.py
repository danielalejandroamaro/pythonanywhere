"""database add queue  is_done

Revision ID: 89667d16d938
Revises: aed804bd2a0e
Create Date: 2023-05-22 16:31:49.465376

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '89667d16d938'
down_revision = 'aed804bd2a0e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('queue', sa.Column('is_done', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('queue', 'is_done')
    # ### end Alembic commands ###
