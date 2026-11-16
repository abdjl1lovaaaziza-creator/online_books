from typing import List, Callable, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.database.models.book import Book
from app.database.models.category import Category
from app.utils.formatting import format_file_size


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Generate keyboard for the 8 supported languages."""
    languages = [
        ("🇬🇧 English", "lang:en"),
        ("🇷🇺 Русский", "lang:ru"),
        ("🇺🇿 O'zbekcha", "lang:uz"),
        ("🇹🇷 Türkçe", "lang:tr"),
        ("🇸🇦 العربية", "lang:ar"),
        ("🇩🇪 Deutsch", "lang:de"),
        ("🇫🇷 Français", "lang:fr"),
        ("🇪🇸 Español", "lang:es"),
    ]
    buttons = []
    for i in range(0, len(languages), 2):
        row = [InlineKeyboardButton(text=languages[i][0], callback_data=languages[i][1])]
        if i + 1 < len(languages):
            row.append(InlineKeyboardButton(text=languages[i + 1][0], callback_data=languages[i + 1][1]))
        buttons.append(row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_search_options_keyboard(user_lang: str = "ru") -> InlineKeyboardMarkup:
    """Inline keyboard for choosing specialized search mode."""
    is_ru = user_lang.startswith("ru")
    btn_title = "📖 По названию" if is_ru else "📖 By Title"
    btn_author = "✍️ По автору" if is_ru else "✍️ By Author"
    btn_keywords = "🏷️ По ключевым словам" if is_ru else "🏷️ By Keywords"
    btn_textbook = "🎓 Искать учебник" if is_ru else "🎓 Search Textbook"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=btn_title, callback_data="search_mode:title"),
                InlineKeyboardButton(text=btn_author, callback_data="search_mode:author"),
            ],
            [
                InlineKeyboardButton(text=btn_keywords, callback_data="search_mode:keywords"),
                InlineKeyboardButton(text=btn_textbook, callback_data="search_mode:textbook"),
            ]
        ]
    )


def get_textbooks_keyboard(user_lang: str = "ru") -> InlineKeyboardMarkup:
    """Generate subject selection keyboard for textbooks."""
    is_ru = user_lang.startswith("ru")

    subjects = [
        ("📐 Высшая математика" if is_ru else "📐 Mathematics", "tb:math"),
        ("⚛️ Физика" if is_ru else "⚛️ Physics", "tb:physics"),
        ("💻 Информатика & IT" if is_ru else "💻 Computer Science", "tb:cs"),
        ("🧪 Химия" if is_ru else "🧪 Chemistry", "tb:chemistry"),
        ("🧬 Биология & Экология" if is_ru else "🧬 Biology", "tb:biology"),
        ("🏛️ Всемирная история" if is_ru else "🏛️ History", "tb:history"),
        ("📊 Экономика & Финансы" if is_ru else "📊 Economics", "tb:economics"),
        ("🌍 Иностранные языки" if is_ru else "🌍 Languages", "tb:languages"),
        ("🩺 Медицина & Анатомия" if is_ru else "🩺 Medicine", "tb:medicine"),
        ("⚖️ Право & Юриспруденция" if is_ru else "⚖️ Law & Justice", "tb:law"),
        ("🎒 Школьная программа" if is_ru else "🎒 School Curriculum", "tb:school"),
        ("🎓 Университетские курсы" if is_ru else "🎓 University Courses", "tb:university"),
    ]

    buttons = []
    for i in range(0, len(subjects), 2):
        row = [InlineKeyboardButton(text=subjects[i][0], callback_data=subjects[i][1])]
        if i + 1 < len(subjects):
            row.append(InlineKeyboardButton(text=subjects[i + 1][0], callback_data=subjects[i + 1][1]))
        buttons.append(row)

    # Custom subject search button
    custom_text = "🔍 Ввести свой предмет" if is_ru else "🔍 Enter Custom Subject"
    buttons.append([InlineKeyboardButton(text=custom_text, callback_data="tb:custom")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_search_results_keyboard(
    books: List[Book],
    page: int,
    total_pages: int,
    query: str,
    action_prefix: str = "search"
) -> InlineKeyboardMarkup:
    """List book search results as selectable inline buttons with pagination."""
    keyboard: List[List[InlineKeyboardButton]] = []

    # One button per book item
    for book in books:
        authors_short = f" ({book.authors[0].name})" if book.authors else ""
        text = f"📖 {book.title[:40]}{authors_short}"
        keyboard.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"book:{book.id}:{action_prefix}:{page}:{query[:15]}"
            )
        ])

    # Pagination navigation controls
    nav_row: List[InlineKeyboardButton] = []
    if page > 1:
        nav_row.append(
            InlineKeyboardButton(
                text="⬅️ Назад" if action_prefix != "en" else "⬅️ Prev",
                callback_data=f"page:{action_prefix}:{page - 1}:{query[:15]}"
            )
        )

    nav_row.append(
        InlineKeyboardButton(
            text=f"{page} / {max(total_pages, 1)}",
            callback_data="noop"
        )
    )

    if page < total_pages:
        nav_row.append(
            InlineKeyboardButton(
                text="Вперед ➡️" if action_prefix != "en" else "Next ➡️",
                callback_data=f"page:{action_prefix}:{page + 1}:{query[:15]}"
            )
        )

    keyboard.append(nav_row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_book_details_keyboard(
    book: Book,
    is_favorite: bool,
    t: Callable,
    back_action: Optional[str] = None,
    back_page: int = 1,
    back_query: str = ""
) -> InlineKeyboardMarkup:
    """Generate actions keyboard for a book view."""
    keyboard: List[List[InlineKeyboardButton]] = []

    # Format download buttons
    for fmt in book.formats:
        size_str = format_file_size(fmt.file_size)
        label = f"📥 Скачать {fmt.format.upper()}"
        if size_str:
            label += f" ({size_str})"
        keyboard.append([
            InlineKeyboardButton(
                text=label,
                callback_data=f"dl:{book.id}:{fmt.id}"
            )
        ])

    # Legal online access / read / preview link
    if book.access_url and book.access_url.startswith(("http://", "https://")):
        keyboard.append([
            InlineKeyboardButton(
                text=t("book.access_btn"),
                url=book.access_url
            )
        ])
    elif book.source_name == "google_books" and book.source_id:
        google_url = f"https://books.google.com/books?id={book.source_id}"
        keyboard.append([
            InlineKeyboardButton(
                text="🌐 Google Книги (Превью / Покупка)",
                url=google_url
            )
        ])

    # Favorite toggle
    fav_text = t("book.remove_fav") if is_favorite else t("book.add_fav")
    keyboard.append([
        InlineKeyboardButton(
            text=fav_text,
            callback_data=f"fav_toggle:{book.id}"
        )
    ])

    # Back to results button if coming from a search or list
    if back_action:
        keyboard.append([
            InlineKeyboardButton(
                text=t("book.back_to_results"),
                callback_data=f"page:{back_action}:{back_page}:{back_query}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_categories_keyboard(
    categories: List[Category],
    user_lang: str = "en"
) -> InlineKeyboardMarkup:
    """Generate categories selection keyboard."""
    keyboard: List[List[InlineKeyboardButton]] = []

    for i in range(0, len(categories), 2):
        row = [
            InlineKeyboardButton(
                text=f"{categories[i].icon} {categories[i].get_name(user_lang)}",
                callback_data=f"cat:{categories[i].id}:1"
            )
        ]
        if i + 1 < len(categories):
            row.append(
                InlineKeyboardButton(
                    text=f"{categories[i + 1].icon} {categories[i + 1].get_name(user_lang)}",
                    callback_data=f"cat:{categories[i + 1].id}:1"
                )
            )
        keyboard.append(row)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_keyboard(t: Callable) -> InlineKeyboardMarkup:
    """Generate admin quick actions keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("admin.btn_stats"), callback_data="admin:stats"),
                InlineKeyboardButton(text=t("admin.btn_broadcast"), callback_data="admin:broadcast"),
            ]
        ]
    )
