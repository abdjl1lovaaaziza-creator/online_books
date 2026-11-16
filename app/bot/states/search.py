from aiogram.fsm.state import State, StatesGroup


class SearchState(StatesGroup):
    """FSM states for search query interaction."""
    waiting_for_query = State()
    waiting_for_title = State()
    waiting_for_author = State()
    waiting_for_keywords = State()
    waiting_for_textbook_subject = State()


class AdminState(StatesGroup):
    """FSM states for administrator actions."""
    waiting_for_broadcast_text = State()
    waiting_for_book_title = State()
    waiting_for_book_url = State()
    waiting_for_category_name = State()
