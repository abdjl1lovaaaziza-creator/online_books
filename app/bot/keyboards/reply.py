from typing import Callable
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu_keyboard(t: Callable, is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Generate the main responsive persistent menu keyboard for Smart Library."""
    keyboard = [
        [
            KeyboardButton(text=t("menu.search")),
            KeyboardButton(text=t("menu.textbooks"))
        ],
        [
            KeyboardButton(text=t("menu.popular")),
            KeyboardButton(text=t("menu.categories"))
        ],
        [
            KeyboardButton(text=t("menu.favorites")),
            KeyboardButton(text=t("menu.about"))
        ]
    ]

    if is_admin:
        keyboard.append([KeyboardButton(text=t("menu.admin"))])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        is_persistent=True
    )
