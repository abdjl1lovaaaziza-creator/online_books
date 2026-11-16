"""Initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-13 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('first_name', sa.String(length=150), nullable=False),
        sa.Column('last_name', sa.String(length=150), nullable=True),
        sa.Column('language_code', sa.String(length=10), server_default='en', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_admin', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'], unique=True)

    # Authors table
    op.create_table(
        'authors',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('birth_year', sa.Integer(), nullable=True),
        sa.Column('death_year', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_authors_name', 'authors', ['name'])

    # Categories table
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('slug', sa.String(length=64), nullable=False),
        sa.Column('name_en', sa.String(length=100), nullable=False),
        sa.Column('name_ru', sa.String(length=100), nullable=False),
        sa.Column('name_uz', sa.String(length=100), nullable=False),
        sa.Column('name_tr', sa.String(length=100), nullable=False),
        sa.Column('name_ar', sa.String(length=100), nullable=False),
        sa.Column('name_de', sa.String(length=100), nullable=False),
        sa.Column('name_fr', sa.String(length=100), nullable=False),
        sa.Column('name_es', sa.String(length=100), nullable=False),
        sa.Column('icon', sa.String(length=10), server_default='📚', nullable=False),
        sa.Column('is_textbook', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_categories_slug', 'categories', ['slug'], unique=True)
    op.create_index('ix_categories_is_textbook', 'categories', ['is_textbook'])

    # Books table
    op.create_table(
        'books',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('original_title', sa.String(length=500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('language', sa.String(length=30), server_default='en', nullable=False),
        sa.Column('publication_year', sa.Integer(), nullable=True),
        sa.Column('publisher', sa.String(length=255), nullable=True),
        sa.Column('isbn', sa.String(length=32), nullable=True),
        sa.Column('cover_url', sa.String(length=1000), nullable=True),
        sa.Column('source_name', sa.String(length=50), nullable=False),
        sa.Column('source_id', sa.String(length=255), nullable=True),
        sa.Column('access_url', sa.String(length=1000), nullable=True),
        sa.Column('license', sa.String(length=100), server_default='Public Domain / Open Access', nullable=False),
        sa.Column('views_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('downloads_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_textbook', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_featured', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_books_title', 'books', ['title'])
    op.create_index('ix_books_isbn', 'books', ['isbn'])
    op.create_index('ix_books_language', 'books', ['language'])
    op.create_index('ix_books_publication_year', 'books', ['publication_year'])
    op.create_index('ix_books_source_id', 'books', ['source_id'])

    # Association: book_authors
    op.create_table(
        'book_authors',
        sa.Column('book_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['authors.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('book_id', 'author_id')
    )
    op.create_index('ix_book_authors_book_author', 'book_authors', ['book_id', 'author_id'])

    # Association: book_categories
    op.create_table(
        'book_categories',
        sa.Column('book_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('book_id', 'category_id')
    )
    op.create_index('ix_book_categories_book_cat', 'book_categories', ['book_id', 'category_id'])

    # Book formats table
    op.create_table(
        'book_formats',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('book_id', sa.Integer(), nullable=False),
        sa.Column('format', sa.String(length=20), nullable=False),
        sa.Column('file_url', sa.String(length=1000), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('telegram_file_id', sa.String(length=255), nullable=True),
        sa.Column('is_direct_download', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_book_formats_book_id', 'book_formats', ['book_id'])
    op.create_index('ix_book_formats_telegram_file_id', 'book_formats', ['telegram_file_id'])

    # Book sources table
    op.create_table(
        'book_sources',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('base_url', sa.String(length=255), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('requires_key', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_book_sources_code', 'book_sources', ['code'], unique=True)

    # Favorites table
    op.create_table(
        'favorites',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('book_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'book_id', name='uq_user_book_favorite')
    )
    op.create_index('ix_favorites_user_id', 'favorites', ['user_id'])
    op.create_index('ix_favorites_book_id', 'favorites', ['book_id'])

    # Downloads table
    op.create_table(
        'downloads',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('book_id', sa.Integer(), nullable=False),
        sa.Column('format', sa.String(length=20), nullable=False),
        sa.Column('telegram_file_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_downloads_user_id', 'downloads', ['user_id'])
    op.create_index('ix_downloads_book_id', 'downloads', ['book_id'])

    # Search history table
    op.create_table(
        'search_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('query', sa.String(length=255), nullable=False),
        sa.Column('filter_type', sa.String(length=50), nullable=True),
        sa.Column('result_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_search_history_user_id', 'search_history', ['user_id'])

    # Admin logs table
    op.create_table(
        'admin_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('admin_telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_admin_logs_admin_telegram_id', 'admin_logs', ['admin_telegram_id'])


def downgrade() -> None:
    op.drop_table('admin_logs')
    op.drop_table('search_history')
    op.drop_table('downloads')
    op.drop_table('favorites')
    op.drop_table('book_sources')
    op.drop_table('book_formats')
    op.drop_table('book_categories')
    op.drop_table('book_authors')
    op.drop_table('books')
    op.drop_table('categories')
    op.drop_table('authors')
    op.drop_table('users')
