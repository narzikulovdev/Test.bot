from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from data.config import botTOKEN
from .middleware import SimpleMiddleware


bot = Bot(token=botTOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(SimpleMiddleware())

# Импорт handlers для их регистрации
from . import handlers
