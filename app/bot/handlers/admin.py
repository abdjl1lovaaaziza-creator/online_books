import asyncio
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.config import settings
from app.bot.filters.admin import IsAdminFilter
from app.bot.states.search import AdminState
from app.bot.keyboards.inline import get_admin_keyboard
from app.database.repositories.user import UserRepository
from app.database.repositories.book import BookRepository
from app.database.repositories.category import CategoryRepository
from app.database.repositories.download import DownloadRepository
from app.services.cache import cache

router = Router(name="admin")
router.message.filter(IsAdminFilter())
router.callback_query.filter(IsAdminFilter())


@router.message(Command("admin"))
async def cmd_admin(message: Message, session: AsyncSession, t):
    """Admin dashboard command."""
    user_repo = UserRepository(session)
    book_repo = BookRepository(session)
    dl_repo = DownloadRepository(session)

    total_users = await user_repo.count_total_users()
    active_users = await user_repo.count_active_users()
    total_books = await book_repo.count_total_books()
    total_dls = await dl_repo.count_total_downloads()

    stats_text = t(
        "admin.stats",
        total_users=total_users,
        active_users=active_users,
        total_books=total_books,
        total_downloads=total_dls,
        redis_status=cache.status_str
    )

    await message.answer(
        f"{t('admin.title')}\n\n{stats_text}",
        reply_markup=get_admin_keyboard(t),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin:stats")
async def cb_admin_stats(callback: CallbackQuery, session: AsyncSession, t):
    """Refresh admin stats."""
    user_repo = UserRepository(session)
    book_repo = BookRepository(session)
    dl_repo = DownloadRepository(session)

    total_users = await user_repo.count_total_users()
    active_users = await user_repo.count_active_users()
    total_books = await book_repo.count_total_books()
    total_dls = await dl_repo.count_total_downloads()

    stats_text = t(
        "admin.stats",
        total_users=total_users,
        active_users=active_users,
        total_books=total_books,
        total_downloads=total_dls,
        redis_status=cache.status_str
    )

    await callback.message.edit_text(
        f"{t('admin.title')}\n\n{stats_text}",
        reply_markup=get_admin_keyboard(t),
        parse_mode="HTML"
    )
    await callback.answer("Stats updated!")


@router.callback_query(F.data == "admin:broadcast")
async def cb_admin_broadcast(callback: CallbackQuery, state: FSMContext, t):
    """Prompt for broadcast announcement text."""
    await state.set_state(AdminState.waiting_for_broadcast_text)
    await callback.message.answer(t("admin.broadcast_prompt"), parse_mode="HTML")
    await callback.answer()


@router.message(AdminState.waiting_for_broadcast_text)
async def process_broadcast_message(message: Message, state: FSMContext, bot: Bot, session: AsyncSession, t):
    """Send broadcast message to all active users."""
    text = message.text
    await state.clear()

    user_repo = UserRepository(session)
    user_ids = await user_repo.get_all_active_telegram_ids()

    status_msg = await message.answer(t("admin.broadcast_started", total=len(user_ids)), parse_mode="HTML")

    sent = 0
    failed = 0
    for uid in user_ids:
        try:
            await bot.send_message(chat_id=uid, text=text, parse_mode="HTML")
            sent += 1
            await asyncio.sleep(0.05)  # Telegram broadcast throttling safe sleep
        except Exception as e:
            failed += 1
            logger.warning(f"Broadcast failed to {uid}: {e}")

    await status_msg.edit_text(
        t("admin.broadcast_done", sent=sent, failed=failed),
        parse_mode="HTML"
    )


@router.message(Command("block"))
async def cmd_block_user(message: Message, session: AsyncSession):
    """Block user by Telegram ID: /block <telegram_id>"""
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Usage: <code>/block &lt;telegram_id&gt;</code>", parse_mode="HTML")
        return

    target_id = int(parts[1])
    user_repo = UserRepository(session)
    updated = await user_repo.set_active_status(target_id, is_active=False)
    await session.commit()

    if updated:
        await message.answer(f"⛔ User <code>{target_id}</code> has been blocked.", parse_mode="HTML")
    else:
        await message.answer(f"User <code>{target_id}</code> not found.", parse_mode="HTML")


@router.message(Command("unblock"))
async def cmd_unblock_user(message: Message, session: AsyncSession):
    """Unblock user by Telegram ID: /unblock <telegram_id>"""
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Usage: <code>/unblock &lt;telegram_id&gt;</code>", parse_mode="HTML")
        return

    target_id = int(parts[1])
    user_repo = UserRepository(session)
    updated = await user_repo.set_active_status(target_id, is_active=True)
    await session.commit()

    if updated:
        await message.answer(f"✅ User <code>{target_id}</code> has been unblocked.", parse_mode="HTML")
    else:
        await message.answer(f"User <code>{target_id}</code> not found.", parse_mode="HTML")
