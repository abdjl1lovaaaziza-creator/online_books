from typing import List, Optional
from sqlalchemy import (
    String, Integer, Text, Boolean, Table, Column, ForeignKey, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base, TimestampMixin

# Association Tables
book_authors = Table(
    "book_authors",
    Base.metadata,
    Column("book_id", ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
    Column("author_id", ForeignKey("authors.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_book_authors_book_author", "book_id", "author_id")
)

book_categories = Table(
    "book_categories",
    Base.metadata,
    Column("book_id", ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_book_categories_book_cat", "book_id", "category_id")
)


class Book(Base, TimestampMixin):
    """Core book model storing comprehensive metadata and source linkage."""
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), index=True, nullable=False)
    original_title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(30), default="en", index=True, nullable=False)
    publication_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    publisher: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    isbn: Mapped[Optional[str]] = mapped_column(String(32), index=True, nullable=True)
    cover_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Provider metadata
    source_name: Mapped[str] = mapped_column(String(50), nullable=False)
    source_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    access_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    license: Mapped[str] = mapped_column(String(100), default="Public Domain / Open Access", nullable=False)

    # Statistics & Flags
    views_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    downloads_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_textbook: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)

    # Relationships
    authors: Mapped[List["Author"]] = relationship("Author", secondary=book_authors, back_populates="books", lazy="selectin")
    categories: Mapped[List["Category"]] = relationship("Category", secondary=book_categories, back_populates="books", lazy="selectin")
    formats: Mapped[List["BookFormat"]] = relationship("BookFormat", back_populates="book", cascade="all, delete-orphan", lazy="selectin")
    favorites: Mapped[List["Favorite"]] = relationship("Favorite", back_populates="book", cascade="all, delete-orphan")
    downloads: Mapped[List["Download"]] = relationship("Download", back_populates="book", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Book id={self.id} title={self.title[:30]!r} source={self.source_name}>"
