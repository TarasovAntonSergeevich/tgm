import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault

from config import config
from database import dispose_db, init_db
from handlers import router

logger = logging.getLogger(__name__)

USER_COMMANDS = [BotCommand(command="start", description="Оставить заявку")]
ADMIN_COMMANDS = USER_COMMANDS + [BotCommand(command="leads", description="Список заявок")]


async def setup_commands(bot: Bot) -> None:
    await bot.set_my_commands(USER_COMMANDS, scope=BotCommandScopeDefault())
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.set_my_commands(ADMIN_COMMANDS, scope=BotCommandScopeChat(chat_id=admin_id))
        except TelegramAPIError as exc:
            # Обычно означает, что админ ещё не нажал /start — команда всё равно работает.
            logger.warning("Не удалось выставить команды для админа %s: %s", admin_id, exc)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )

    await init_db()

    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    try:
        await setup_commands(bot)
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Бот запущен. Админы: %s", ", ".join(map(str, config.ADMIN_IDS)))
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await dispose_db()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен")
