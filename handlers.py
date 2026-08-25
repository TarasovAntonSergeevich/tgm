import html
import logging

from aiogram import F, Router
from aiogram.filters import BaseFilter, Command, CommandObject, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove

from config import config
from database import count_leads, list_leads, save_lead

logger = logging.getLogger(__name__)

router = Router()

MAX_FIELD_LEN = 128
PAGE_SIZE = 20

GREETING = "Есть люди, которые готовы действовать. Кто-то должен навести порядок."
ASK_NAME = "Как вас зовут?"
ASK_CITY = "Приятно познакомиться, {name}! Из какого вы города?"
DONE = "Координатор свяжется с вами в ближайшее время."
NEED_TEXT = "Пожалуйста, отправьте ответ текстом."
TOO_LONG = f"Слишком длинный ответ. Уложитесь, пожалуйста, в {MAX_FIELD_LEN} символов."


class Survey(StatesGroup):
    name = State()
    city = State()


def _clean(text: str) -> str:
    return " ".join(text.split())


class IsAdmin(BaseFilter):
    """Пропускает только пользователей из ADMIN_IDS (.env)."""

    async def __call__(self, message: Message) -> bool:
        return message.from_user is not None and config.is_admin(message.from_user.id)


# --- Админские команды регистрируем первыми, иначе их перехватят FSM-хендлеры ---


@router.message(Command("leads", "get_some_info"), IsAdmin())
async def cmd_leads(message: Message, command: CommandObject) -> None:
    """Список заявок постранично: /leads, /leads 2, /leads 3 ..."""
    page = 1
    if command.args and command.args.strip().isdigit():
        page = max(1, int(command.args.strip()))

    total = await count_leads()
    if total == 0:
        await message.answer("Заявок пока нет.")
        return

    pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    if page > pages:
        await message.answer(f"Такой страницы нет. Всего страниц: {pages}.")
        return

    leads = await list_leads(limit=PAGE_SIZE, offset=(page - 1) * PAGE_SIZE)

    lines = [f"<b>Заявки: {total}</b> (страница {page} из {pages})", ""]
    for i, lead in enumerate(leads, start=(page - 1) * PAGE_SIZE + 1):
        username = f" (@{html.escape(lead.username)})" if lead.username else ""
        lines.append(
            f"{i}. <b>{html.escape(lead.name)}</b> — {html.escape(lead.city)}\n"
            f"    id: <code>{lead.tg_id}</code>{username}\n"
            f"    {lead.created_at:%d.%m.%Y %H:%M} UTC"
        )
    if page < pages:
        lines.append(f"\nСледующая страница: /leads {page + 1}")

    await message.answer("\n".join(lines))


# --- Сценарий пользователя ---


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.set_state(Survey.name)
    await message.answer(GREETING, reply_markup=ReplyKeyboardRemove())
    await message.answer(ASK_NAME)


@router.message(Survey.name, F.text)
async def process_name(message: Message, state: FSMContext) -> None:
    name = _clean(message.text)
    if not name:
        await message.answer(NEED_TEXT)
        return
    if len(name) > MAX_FIELD_LEN:
        await message.answer(TOO_LONG)
        return

    await state.update_data(name=name)
    await state.set_state(Survey.city)
    await message.answer(ASK_CITY.format(name=html.escape(name)))


@router.message(Survey.city, F.text)
async def process_city(message: Message, state: FSMContext) -> None:
    city = _clean(message.text)
    if not city:
        await message.answer(NEED_TEXT)
        return
    if len(city) > MAX_FIELD_LEN:
        await message.answer(TOO_LONG)
        return

    data = await state.get_data()
    await state.clear()

    lead = await save_lead(
        tg_id=message.from_user.id,
        username=message.from_user.username,
        name=data["name"],
        city=city,
    )
    logger.info("Новая заявка: %r", lead)

    await message.answer(DONE, reply_markup=ReplyKeyboardRemove())


@router.message(StateFilter(Survey.name, Survey.city))
async def process_non_text(message: Message) -> None:
    await message.answer(NEED_TEXT)


@router.message()
async def fallback(message: Message, state: FSMContext) -> None:
    """Любое сообщение вне сценария начинает анкету заново."""
    await cmd_start(message, state)
