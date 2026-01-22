from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import SkipHandler
from data import db
import logging

logger = logging.getLogger(__name__)


class SimpleMiddleware(BaseMiddleware):

    async def on_pre_process_message(self, msg: types.Message, data: dict):
        # Проверяем существование пользователя
        is_new_user = not db.Users.isUserExist(msg.from_user.id)
        
        if is_new_user:
            # Добавляем нового пользователя
            db.Users.addUser(msg.from_user.id, msg.from_user.full_name)
            logger.info(f"Новый пользователь: {msg.from_user.id} - {msg.from_user.full_name}")
            # Добавляем флаг нового пользователя в данные
            data['is_new_user'] = True
        else:
            data['is_new_user'] = False
            # Проверяем блокировку
            if db.Users.isBlocked(msg.from_user.id):
                await msg.reply("Ваша учётная запись заблокирована. Пожалуйста, свяжитесь с администратором.")
                raise SkipHandler()


