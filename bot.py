import asyncio
import os
import aiosqlite
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))
DB_PATH = "diary_bot.db"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- Расписание (пример данных, можно редактировать под свою школу) ---
SCHEDULE = {
    "monday": [
        "1. Հայոց լեզու",
        "2. Մաթեմատիկա",
        "3. Ֆիզիկա",
        "4. Պատմություն",
        "5. Օտար լեզու"
    ],
    "tuesday": [
        "1. Գրականություն",
        "2. Հանրահաշիվ",
        "3. Քիմիա",
        "4. Անգլերեն",
        "5. Ֆիզկուլտուրա"
    ],
    "wednesday": [
        "1. Երկրաչափություն",
        "2. Կենսաբանություն",
        "3. Պատմություն",
        "4. Ռուսաց լեզու",
        "5. Ինֆորմատիկա"
    ],
    "thursday": [
        "1. Մաթեմատիկա",
        "2. Հայոց լեզու",
        "3. Աշխարհագրություն",
        "4. Ֆիզիկա",
        "5. Օտար լեզու"
    ],
    "friday": [
        "1. Գրականություն",
        "2. Պատմություն",
        "3. Կենսաբանություն",
        "4. Հասարակագիտություն",
        "5. ՆԶՊ"
    ],
    "saturday": [
        "Այս օրը դասեր նախատեսված չեն:"
    ]
}

DAYS_NAMES = {
    "monday": "Երկուշաբթի",
    "tuesday": "Երեքշաբթի",
    "wednesday": "Չորեքշաբթի",
    "thursday": "Հինգշաբթի",
    "friday": "Ուրբաթ",
    "saturday": "Շաբաթ"
}


# --- Состояния FSM (диалог выбора) ---
class SetupGrade(StatesGroup):
    grade_number = State()
    grade_letter = State()


# --- База данных SQLite ---
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                grade_number INTEGER,
                grade_letter TEXT
            )
        """)
        await db.commit()

async def get_user_grade(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT grade_number, grade_letter FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()

async def save_user_grade(user_id: int, grade_number: int, grade_letter: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, grade_number, grade_letter)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                grade_number = excluded.grade_number,
                grade_letter = excluded.grade_letter
        """, (user_id, grade_number, grade_letter))
        await db.commit()


# --- Клавиатуры ---
def get_grade_numbers_kb() -> InlineKeyboardMarkup:
    # Кнопки классов 1-9 (по 3 в строке)
    rows = []
    current_row = []
    for num in range(1, 10):
        current_row.append(InlineKeyboardButton(text=f"{num}-րդ", callback_data=f"grade_num:{num}"))
        if len(current_row) == 3:
            rows.append(current_row)
            current_row = []
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_grade_letters_kb() -> InlineKeyboardMarkup:
    # Буквы: Ա, Բ, Գ
    keyboard = [
        [
            InlineKeyboardButton(text="Ա", callback_data="grade_let:Ա"),
            InlineKeyboardButton(text="Բ", callback_data="grade_let:Բ"),
            InlineKeyboardButton(text="Գ", callback_data="grade_let:Գ")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_days_kb() -> InlineKeyboardMarkup:
    # Дни недели (по 2 в строке)
    keyboard = [
        [
            InlineKeyboardButton(text="Երկուշաբթի", callback_data="day:monday"),
            InlineKeyboardButton(text="Երեքշաբթի", callback_data="day:tuesday")
        ],
        [
            InlineKeyboardButton(text="Չորեքշաբթի", callback_data="day:wednesday"),
            InlineKeyboardButton(text="Հինգշաբթի", callback_data="day:thursday")
        ],
        [
            InlineKeyboardButton(text="Ուրբաթ", callback_data="day:friday"),
            InlineKeyboardButton(text="Շաբաթ", callback_data="day:saturday")
        ],
        [
            InlineKeyboardButton(text="Փոխել դասարանը", callback_data="change_grade")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# --- Обработчики команд и диалогов ---
@dp.message(CommandStart())
async def handle_start(message: Message, state: FSMContext):
    user_grade = await get_user_grade(message.from_user.id)
    if user_grade:
        grade_num, grade_let = user_grade
        await message.answer(
            f"Բարի գալուստ: Դուք ընտրել եք {grade_num}-{grade_let} դասարանը:\n"
            "Ընտրեք շաբաթվա օրը դասացուցակը տեսնելու համար:",
            reply_markup=get_days_kb()
        )
    else:
        await state.set_state(SetupGrade.grade_number)
        await message.answer(
            "Բարև ձեզ: Խնդրում ենք նախ ընտրել ձեր դասարանը (1-9):",
            reply_markup=get_grade_numbers_kb()
        )

@dp.message(Command("reset"))
async def handle_reset(message: Message, state: FSMContext):
    await state.set_state(SetupGrade.grade_number)
    await message.answer(
        "Ընտրեք ձեր դասարանը (1-9):",
        reply_markup=get_grade_numbers_kb()
    )

@dp.callback_query(SetupGrade.grade_number, F.data.startswith("grade_num:"))
async def handle_grade_num(call: CallbackQuery, state: FSMContext):
    grade_num = int(call.data.split(":")[1])
    await state.update_data(grade_number=grade_num)
    await state.set_state(SetupGrade.grade_letter)
    await call.message.edit_text(
        f"Ընտրված է՝ {grade_num}-րդ դասարան:\n"
        "Այժմ ընտրեք դասարանի տառը (Ա, Բ, Գ):",
        reply_markup=get_grade_letters_kb()
    )
    await call.answer()

@dp.callback_query(SetupGrade.grade_letter, F.data.startswith("grade_let:"))
async def handle_grade_let(call: CallbackQuery, state: FSMContext):
    grade_letter = call.data.split(":")[1]
    data = await state.get_data()
    grade_number = data.get("grade_number")
    
    await save_user_grade(call.from_user.id, grade_number, grade_letter)
    await state.clear()
    
    await call.message.edit_text(
        f"Կարգավորումները պահպանված են: Ձեր դասարանն է՝ {grade_number}-{grade_letter}:\n\n"
        "Ընտրեք շաբաթվա օրը դասացուցակը դիտելու համար:",
        reply_markup=get_days_kb()
    )
    await call.answer()

@dp.callback_query(F.data.startswith("day:"))
async def handle_day_selection(call: CallbackQuery):
    day_key = call.data.split(":")[1]
    user_grade = await get_user_grade(call.from_user.id)
    
    if not user_grade:
        await call.message.edit_text(
            "Դասարանը ընտրված չէ: Խնդրում ենք ընտրել դասարանը:",
            reply_markup=get_grade_numbers_kb()
        )
        await call.answer()
        return

    grade_num, grade_let = user_grade
    day_title = DAYS_NAMES.get(day_key, "")
    lessons = SCHEDULE.get(day_key, ["Դասացուցակը դեռ լրացված չէ:"])
    schedule_text = "\n".join(lessons)

    text = (
        f"Դասարան՝ {grade_num}-{grade_let}\n"
        f"Օր՝ {day_title}\n\n"
        f"Դասացուցակ՝\n{schedule_text}\n\n"
        "Ընտրեք այլ օր կամ փոխեք դասարանը:"
    )

    await call.message.edit_text(text, reply_markup=get_days_kb())
    await call.answer()

@dp.callback_query(F.data == "change_grade")
async def handle_change_grade(call: CallbackQuery, state: FSMContext):
    await state.set_state(SetupGrade.grade_number)
    await call.message.edit_text(
        "Ընտրեք նոր դասարանը (1-9):",
        reply_markup=get_grade_numbers_kb()
    )
    await call.answer()


# --- Веб-сервер для поддержки активности Render (Health check) ---
async def handle_health_check(request):
    return web.Response(text="Bot is operational")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

async def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN չի գտնվել:")

    await init_db()
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
