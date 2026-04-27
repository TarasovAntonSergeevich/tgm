import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat

from config import config
import handlers as handlers_module

logging.basicConfig(level=logging.INFO)


async def setup_commands(bot: Bot):
    await bot.delete_my_commands(scope=BotCommandScopeDefault())
    for admin_id in config.ADMIN_IDS:
        await bot.set_my_commands(
            commands=[BotCommand(command="get_some_info", description="Получить данные")],
            scope=BotCommandScopeChat(chat_id=admin_id)
        )


async def main():
    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await setup_commands(bot)
    dp = Dispatcher()
    dp.include_router(handlers_module.router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())