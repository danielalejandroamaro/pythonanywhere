"""database add carr

Revision ID: ea93af59ee92
Revises: e8693da9369b
Create Date: 2023-05-20 16:30:31.885691

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'ea93af59ee92'
down_revision = 'e8693da9369b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('car',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('chapa', sa.String(length=20), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_column('person', 'chapa')
    op.add_column('queue', sa.Column('persone_id', sa.Integer(), nullable=False))
    op.add_column('queue', sa.Column('car_id', sa.Integer(), nullable=False))
    op.drop_constraint('queue_ibfk_1', 'queue', type_='foreignkey')
    op.create_foreign_key(None, 'queue', 'person', ['persone_id'], ['id'])
    op.create_foreign_key(None, 'queue', 'car', ['car_id'], ['id'])
    op.drop_column('queue', 'persone')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('queue', sa.Column('persone', mysql.INTEGER(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'queue', type_='foreignkey')
    op.drop_constraint(None, 'queue', type_='foreignkey')
    op.create_foreign_key('queue_ibfk_1', 'queue', 'person', ['persone'], ['id'])
    op.drop_column('queue', 'car_id')
    op.drop_column('queue', 'persone_id')
    op.add_column('person', sa.Column('chapa', mysql.VARCHAR(length=20), nullable=True))
    op.drop_table('car')
    # ### end Alembic commands ###
