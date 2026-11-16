from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings

# Initialize Bot instance with HTML default parsing
bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Initialize Dispatcher
dp = Dispatcher(storage=MemoryStorage())
