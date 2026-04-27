from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import save_user, get_all_users
from config import config

router = Router()

CATEGORIES = {
    "cat1": {"name": "Категория 1", "items": ["Товар 1", "Товар 2", "Товар 3", "Товар 4"]},
    "cat2": {"name": "Категория 2", "items": ["Товар A", "Товар B", "Товар C", "Товар D"]},
}


class SurveyStates(StatesGroup):
    waiting_for_question_answer = State()
    waiting_for_category = State()
    waiting_for_item = State()
    waiting_for_name = State()
    waiting_for_city = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await message.answer("Привет! Ответьте на вопрос: Какой ваш любимый цвет?")
    await state.set_state(SurveyStates.waiting_for_question_answer)


@router.message(SurveyStates.waiting_for_question_answer)
async def process_question_answer(message: Message, state: FSMContext):
    await state.update_data(question_answer=message.text)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=CATEGORIES["cat1"]["name"])],
            [KeyboardButton(text=CATEGORIES["cat2"]["name"])],
        ],
        resize_keyboard=True
    )
    await message.answer("Выберите категорию:", reply_markup=keyboard)
    await state.set_state(SurveyStates.waiting_for_category)


@router.message(SurveyStates.waiting_for_category)
async def process_category(message: Message, state: FSMContext):
    selected_cat = None
    for key, cat in CATEGORIES.items():
        if cat["name"] == message.text:
            selected_cat = cat
            await state.update_data(selected_category=key)
            break

    if not selected_cat:
        await message.answer("Пожалуйста, выберите категорию из списка.")
        return

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=item)] for item in selected_cat["items"]],
        resize_keyboard=True
    )
    await message.answer(f"Товары в категории {selected_cat['name']}:\nВыберите товар:", reply_markup=keyboard)
    await state.set_state(SurveyStates.waiting_for_item)


@router.message(SurveyStates.waiting_for_item)
async def process_item(message: Message, state: FSMContext):
    data = await state.get_data()
    selected_cat = CATEGORIES.get(data.get("selected_category"))

    if not selected_cat or message.text not in selected_cat["items"]:
        await message.answer("Пожалуйста, выберите товар из списка.")
        return

    await state.update_data(selected_item=message.text)
    await message.answer("Представьтесь, пожалуйста (ваше имя):")
    await state.set_state(SurveyStates.waiting_for_name)


@router.message(SurveyStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Из какого вы города?")
    await state.set_state(SurveyStates.waiting_for_city)


@router.message(SurveyStates.waiting_for_city)
async def process_city(message: Message, state: FSMContext):
    data = await state.get_data()
    tg_username = message.from_user.username or message.from_user.first_name

    save_user(
        tg_username=tg_username,
        display_name=data["name"],
        city=message.text,
        category_choice=f"{data.get('selected_category')}:{data.get('selected_item', '')}"
    )

    await message.answer("Отлично! Мы с вами свяжемся в ближайшее время!")
    await state.clear()


@router.message(F.text.startswith("/get_some_info"))
async def admin_panel(message: Message):
    if message.from_user.id not in config.ADMIN_IDS:
        return

    users = get_all_users()
    if not users:
        await message.answer("Нет записей.")
        return

    text = "Список пользователей:\n\n"
    for user in users:
        text += f"@{user.tg_username}\n"
        text += f"  Имя: {user.display_name}\n"
        text += f"  Город: {user.city}\n"
        text += f"  Выбор: {user.category_choice or 'N/A'}\n"
        text += f"  Дата: {user.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"

    await message.answer(text)