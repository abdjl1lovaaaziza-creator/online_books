import pytest
from app.bot.keyboards.reply import get_main_menu_keyboard
from app.bot.keyboards.inline import (
    get_search_options_keyboard,
    get_textbooks_keyboard,
    get_book_details_keyboard
)
from app.localization.manager import LocalizationManager
from app.utils.formatting import format_book_caption_html
from app.database.models.book import Book
from app.database.models.author import Author
from app.database.models.format import BookFormat


def test_main_menu_buttons_russian():
    """Verify the 6 user-specified main menu buttons are correctly generated in Russian."""
    manager = LocalizationManager()
    t_ru = lambda key, **kwargs: manager.get(key, lang="ru", **kwargs)

    kb = get_main_menu_keyboard(t_ru, is_admin=False)
    # Check button texts
    button_texts = [btn.text for row in kb.keyboard for btn in row]

    assert "📚 Найти книгу" in button_texts
    assert "🎓 Учебники" in button_texts
    assert "🔥 Популярные книги" in button_texts
    assert "📂 Категории" in button_texts
    assert "⭐ Избранное" in button_texts
    assert "ℹ️ О боте" in button_texts
    assert len(button_texts) == 6


def test_search_options_keyboard():
    """Verify dedicated search criteria options (Title, Author, Keywords, Textbook)."""
    kb = get_search_options_keyboard(user_lang="ru")
    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row]

    assert "search_mode:title" in callbacks
    assert "search_mode:author" in callbacks
    assert "search_mode:keywords" in callbacks
    assert "search_mode:textbook" in callbacks


def test_textbooks_keyboard_subjects():
    """Verify textbooks subjects keyboard includes disciplines and custom search."""
    kb = get_textbooks_keyboard(user_lang="ru")
    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row]

    assert "tb:math" in callbacks
    assert "tb:physics" in callbacks
    assert "tb:cs" in callbacks
    assert "tb:chemistry" in callbacks
    assert "tb:custom" in callbacks


def test_book_formatting_russian():
    """Verify book card is nicely formatted with Russian headers and metadata."""
    book = Book(
        id=1,
        title="Война и мир",
        publication_year=1869,
        language="ru",
        publisher="Русский Вестник",
        isbn="9785170908882",
        source_name="google_books",
        license="Общественное достояние",
        description="Роман-эпопея Льва Толстого об Отечественной войне 1812 года."
    )
    author = Author(id=1, name="Лев Николаевич Толстой")
    book.authors = [author]
    fmt = BookFormat(id=1, book_id=1, format="pdf", file_size=15 * 1024 * 1024)
    book.formats = [fmt]

    caption = format_book_caption_html(book, lang="ru")
    assert "Война и мир" in caption
    assert "Лев Николаевич Толстой" in caption
    assert "1869" in caption
    assert "Автор(ы):" in caption
    assert "Год выпуска:" in caption
    assert "Издательство:" in caption
    assert "9785170908882" in caption


def test_book_details_keyboard_legal_links():
    """Verify legal sources links in book details keyboard."""
    manager = LocalizationManager()
    t = lambda key, **kwargs: manager.get(key, lang="ru", **kwargs)

    book = Book(
        id=99,
        title="Тестовая книга",
        source_name="google_books",
        access_url="https://books.google.com/books?id=test123",
        license="Open Access"
    )
    book.formats = []

    kb = get_book_details_keyboard(book, is_favorite=False, t=t)
    urls = [btn.url for row in kb.inline_keyboard for btn in row if btn.url]

    assert "https://books.google.com/books?id=test123" in urls
