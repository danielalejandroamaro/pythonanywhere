"""database udapte

Revision ID: c2e876ce77f3
Revises: a207a815aada
Create Date: 2023-05-25 13:20:33.375465

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c2e876ce77f3'
down_revision = 'a207a815aada'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('qr_table', 'count')
    op.add_column('queue', sa.Column('qr_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'queue', 'qr_table', ['qr_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'queue', type_='foreignkey')
    op.drop_column('queue', 'qr_id')
    op.add_column('qr_table', sa.Column('count', sa.INTEGER(), server_default=sa.text('0'), autoincrement=False, nullable=False))
    # ### end Alembic commands ###
