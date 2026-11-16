import html
from typing import Optional, List
from app.database.models.book import Book


def format_file_size(size_bytes: Optional[int]) -> str:
    """Format bytes into readable string (KB, MB, GB)."""
    if not size_bytes or size_bytes <= 0:
        return ""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def escape_html(text: Optional[str]) -> str:
    """Safely escape text for Telegram HTML parse_mode."""
    if not text:
        return ""
    return html.escape(str(text))


LABELS = {
    "ru": {
        "authors": "Автор(ы)",
        "year": "Год выпуска",
        "language": "Язык",
        "publisher": "Издательство",
        "isbn": "ISBN",
        "formats": "Доступные форматы",
        "license": "Лицензия",
        "source": "Источник",
        "description": "Краткое описание",
        "online_only": "Чтение онлайн / Легальный просмотр",
        "unknown": "Не указан",
        "no_description": "Описание для этой книги отсутствует."
    },
    "en": {
        "authors": "Author(s)",
        "year": "Year",
        "language": "Language",
        "publisher": "Publisher",
        "isbn": "ISBN",
        "formats": "Formats",
        "license": "License",
        "source": "Source",
        "description": "Description",
        "online_only": "Online Access / Reading Only",
        "unknown": "Unknown",
        "no_description": "No description provided."
    }
}


def format_book_caption_html(book: Book, lang: str = "en") -> str:
    """
    Format a complete, professional book card using Telegram HTML markup.
    Localizes labels based on user's active language (Russian / English).
    """
    locale_labels = LABELS.get(lang[:2].lower(), LABELS["en"])

    title = escape_html(book.title)
    authors = ", ".join(escape_html(a.name) for a in book.authors) if book.authors else locale_labels["unknown"]
    year = str(book.publication_year) if book.publication_year else locale_labels["unknown"]
    language = escape_html(book.language.upper())
    publisher = escape_html(book.publisher or locale_labels["unknown"])
    isbn = escape_html(book.isbn or locale_labels["unknown"])

    formats_list = [f.format.upper() for f in book.formats]
    formats_str = ", ".join(formats_list) if formats_list else locale_labels["online_only"]

    license_str = escape_html(book.license)
    source = escape_html(book.source_name.replace("_", " ").title())

    desc_raw = book.description or locale_labels["no_description"]
    if len(desc_raw) > 380:
        desc_raw = desc_raw[:377] + "..."
    description = escape_html(desc_raw)

    text = (
        f"📖 <b>{title}</b>\n\n"
        f"✍️ <b>{locale_labels['authors']}:</b> {authors}\n"
        f"📅 <b>{locale_labels['year']}:</b> {year}\n"
        f"🌐 <b>{locale_labels['language']}:</b> {language}\n"
        f"🏢 <b>{locale_labels['publisher']}:</b> {publisher}\n"
        f"🔢 <b>{locale_labels['isbn']}:</b> <code>{isbn}</code>\n"
        f"📑 <b>{locale_labels['formats']}:</b> {formats_str}\n"
        f"⚖️ <b>{locale_labels['license']}:</b> {license_str}\n"
        f"🏛️ <b>{locale_labels['source']}:</b> {source}\n\n"
        f"📝 <b>{locale_labels['description']}:</b>\n<i>{description}</i>"
    )
    return text
