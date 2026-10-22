import asyncio
import os
import aiosqlite
from aiohttp import web, ClientSession
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
from aiogram.exceptions import TelegramBadRequest

TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("AQ.Ab8RN6IZphlNew9VLwAau4gBh54NR7M2FBiSOPKzSZohTAV4Ug") # Ключ от Gemini API
PORT = int(os.getenv("PORT", 8080))
DB_PATH = "diary_bot.db"

# Используем быструю и легкую модель Gemini
GEMINI_MODEL = "gemini-2.5-flash-lite"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- Расписание разделено на каждый класс отдельно (1-Ա .. 9-Գ) ---
SCHEDULE = {
    "1-Ա": {
        "monday": ["1. Այբբենարան", "2. Մաթեմատիկա", "3. Կերպարվեստ", "4. Ֆիզկուլտուրա"],
        "tuesday": ["1. Այբբենարան", "2. Մաթեմատիկա", "3. Երաժշտություն", "4. Տեխնոլոգիա"],
        "wednesday": ["1. Այբբենարան", "2. Մաթեմատիկա", "3. Ես և շրջակա աշխարհը", "4. Ֆիզկուլտուրա"],
        "thursday": ["1. Այբբենարան", "2. Մաթեմատիկա", "3. Կերպարվեստ", "4. Շախմատ"],
        "friday": ["1. Այբբենարան", "2. Մաթեմատիկա", "3. Երաժշտություն", "4. Տեխնոլոգիա"],
        "saturday": ["Այս օրը դասեր նախատեսված չեն:"]
    },
    "1-Բ": {
        "monday": ["1. Մաթեմատիկա", "2. Այբբենարան", "3. Ֆիզկուլտուրա", "4. Կերպարվեստ"],
        "tuesday": ["1. Այբբենարան", "2. Մաթեմատիկա", "3. Տեխնոլոգիա", "4. Երաժշտություն"],
        "wednesday": ["1. Մաթեմատիկա", "2. Այբբենարան", "3. Ֆիզկուլտուրա", "4. Շախմատ"],
        "thursday": ["1. Այբբենարան", "2. Մաթեմատիկա", "3. Ես և շրջակա աշխարհը", "4. Կերպարվեստ"],
        "friday": ["1. Այբբենարան", "2. Մաթեմատիկա", "3. Տեխնոլոգիա", "4. Երաժշտություն"],
        "saturday": ["Այս օրը դասեր նախատեսված չեն:"]
    },
    "1-Գ": {
        "monday": ["1. Այբբենարան", "2. Մաթեմատիկա", "3. Շախմատ", "4. Ֆիզկուլտուրա"],
        "tuesday": ["1. Մաթեմատիկա", "2. Այբբենարան", "3. Երաժշտություն", "4. Կերպարվեստ"],
        "wednesday": ["1. Այբբենարան", "2. Մաթեմատիկա", "3. Տեխնոլոգիա", "4. Ֆիզկուլտուրա"],
        "thursday": ["1. Մաթեմատիկա", "2. Այբբենարան", "3. Ես և շրջակա աշխարհը", "4. Շախմատ"],
        "friday": ["1. Այբբենարան", "2. Մաթեմատիկա", "3. Կերպարվեստ", "4. Երաժշտություն"],
        "saturday": ["Այս օրը դասեր նախատեսված չեն:"]
    },
    "2-Ա": {
        "monday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Ռուսաց լեզու", "4. Ֆիզկուլտուրա"],
        "tuesday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Երաժշտություն", "4. Կերպարվեստ"],
        "wednesday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Ես և շրջակա աշխարհը", "4. Շախմատ"],
        "thursday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Ռուսաց լեզու", "4. Տեխնոլոգիա"],
        "friday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Ֆիզկուլտուրա", "4. Շախմատ"],
        "saturday": ["Այս օրը դասեր նախատեսված չեն:"]
    },
    "2-Բ": {
        "monday": ["1. Մաթեմատիկա", "2. Մայրենի", "3. Ֆիզկուլտուրա", "4. Ռուսաց լեզու"],
        "tuesday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Կերպարվեստ", "4. Երաժշտություն"],
        "wednesday": ["1. Մաթեմատիկա", "2. Մայրենի", "3. Շախմատ", "4. Ես և շրջակա աշխարհը"],
        "thursday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Տեխնոլոգիա", "4. Ռուսաց լեզու"],
        "friday": ["1. Մաթեմատիկա", "2. Մայրենի", "3. Շախմատ", "4. Ֆիզկուլտուրա"],
        "saturday": ["Այս օրը դասեր նախատեսված չեն:"]
    },
    "2-Գ": {
        "monday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Շախմատ", "4. Ռուսաց լեզու"],
        "tuesday": ["1. Մաթեմատիկա", "2. Մայրենի", "3. Ֆիզկուլտուրա", "4. Կերպարվեստ"],
        "wednesday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Ռուսաց լեզու", "4. Երաժշտություն"],
        "thursday": ["1. Մաթեմատիկա", "2. Մայրենի", "3. Ես և շրջակա աշխարհը", "4. Տեխնոլոգիա"],
        "friday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Ֆիզկուլտուրա", "4. Շախմատ"],
        "saturday": ["Այս օրը դասեր նախատեսված չեն:"]
    },
    "3-Ա": {
        "monday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Օտար լեզու", "4. Ֆիզկուլտուրա", "5. Կերպարվեստ"],
        "tuesday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Ռուսաց լեզու", "4. Երաժշտություն", "5. Շախմատ"],
        "wednesday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Ես և շրջակա աշխարհը", "4. Օտար լեզու", "5. Տեխնոլոգիա"],
        "thursday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Ռուսաց լեզու", "4. Ֆիզկուլտուրա", "5. Շախմատ"],
        "friday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Օտար լեզու", "4. Ես և շրջակա աշխարհը", "5. Տեխնոլոգիա"],
        "saturday": ["Այս օրը դասեր նախատեսված չեն:"]
    },
    "3-Բ": {
        "monday": ["1. Մաթեմատիկա", "2. Մայրենի", "3. Ռուսաց լեզու", "4. Ֆիզկուլտուրա", "5. Երաժշտություն"],
        "tuesday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Օտար լեզու", "4. Կերպարվեստ", "5. Շախմատ"],
        "wednesday": ["1. Մաթեմատիկա", "2. Մայրենի", "3. Ռուսաց լեզու", "4. Ես և շրջակա աշխարհը", "5. Տեխնոլոգիա"],
        "thursday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Օտար լեզու", "4. Շախմատ", "5. Ֆիզկուլտուրա"],
        "friday": ["1. Մաթեմատիկա", "2. Մայրենի", "3. Ես և շրջակա աշխարհը", "4. Ռուսաց լեզու", "5. Տեխնոլոգիա"],
        "saturday": ["Այս օրը դասեր նախատեսված չեն:"]
    },
    "3-Գ": {
        "monday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Ես և շրջակա աշխարհը", "4. Օտար լեզու", "5. Ֆիզկուլտուրա"],
        "tuesday": ["1. Մաթեմատիկա", "2. Մայրենի", "3. Ռուսաց լեզու", "4. Շախմատ", "5. Կերպարվեստ"],
        "wednesday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Օտար լեզու", "4. Երաժշտություն", "5. Տեխնոլոգիա"],
        "thursday": ["1. Մաթեմատիկա", "2. Մայրենի", "3. Ռուսաց լեզու", "4. Ես և շրջակա աշխարհը", "5. Ֆիզկուլտուրա"],
        "friday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Շախմատ", "4. Ռուսաց լեզու", "5. Տեխնոլոգիա"],
        "saturday": ["Այս օրը դասեր նախատեսված չեն:"]
    },
    "4-Ա": {
        "monday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Ռուսաց լեզու", "4. Օտար լեզու", "5. Ֆիզկուլտուրա"],
        "tuesday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Ես և շրջակա աշխարհը", "4. Շախմատ", "5. Կերպարվեստ"],
        "wednesday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Ռուսաց լեզու", "4. Երաժշտություն", "5. Տեխնոլոգիա"],
        "thursday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Օտար լեզու", "4. Ես և շրջակա աշխարհը", "5. Ֆիզկուլտուրա"],
        "friday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Ռուսաց լեզու", "4. Օտար լեզու", "5. Շախմատ"],
        "saturday": ["Այս օրը դասեր նախատեսված չեն:"]
    },
    "4-Բ": {
        "monday": ["1. Մաթեմատիկա", "2. Մայրենի", "3. Օտար լեզու", "4. Ռուսաց լեզու", "5. Ֆիզկուլտուրա"],
        "tuesday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Շախմատ", "4. Ես և շրջակա աշխարհը", "5. Երաժշտություն"],
        "wednesday": ["1. Մաթեմատիկա", "2. Մայրենի", "3. Ռուսաց լեզու", "4. Կերպարվեստ", "5. Տեխնոլոգիա"],
        "thursday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Ես և շրջակա աշխարհը", "4. Օտար լեզու", "5. Ֆիզկուլտուրա"],
        "friday": ["1. Մաթեմատիկա", "2. Մայրենի", "3. Օտար լեզու", "4. Ռուսաց լեզու", "5. Շախմատ"],
        "saturday": ["Այս օրը դասեր նախատեսված չեն:"]
    },
    "4-Գ": {
        "monday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Ֆիզկուլտուրա", "4. Ռուսաց լեզու", "5. Օտար լեզու"],
        "tuesday": ["1. Մաթեմատիկա", "2. Մայրենի", "3. Ես և շրջակա աշխարհը", "4. Կերպարվեստ", "5. Շախմատ"],
        "wednesday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Օտար լեզու", "4. Տեխնոլոգիա", "5. Երաժշտություն"],
        "thursday": ["1. Մաթեմատիկա", "2. Մայրենի", "3. Ռուսաց լեզու", "4. Ֆիզկուլտուրա", "5. Ես և շրջակա աշխարհը"],
        "friday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Շախմատ", "4. Ռուսաց լեզու", "5. Օտար լեզու"],
        "saturday": ["Այս օրը դասեր նախատեսված չեն:"]
    },
    "5-Ա": {
        "monday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Բնագիտություն", "4. Ռուսաց լեզու", "5. Ֆիզկուլտուրա"],
        "tuesday": ["1. Մաթեմատիկա", "2. Մայրենի", "3. Հայրենագիտություն", "4. Օտար լեզու", "5. Կերպարվեստ"],
        "wednesday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Ռուսաց լեզու", "4. Երաժշտություն", "5. Տեխնոլոգիա"],
        "thursday": ["1. Մաթեմատիկա", "2. Մայրենի", "3. Բնագիտություն", "4. Օտար լեզու", "5. Ֆիզկուլտուրա"],
        "friday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Հայրենագիտություն", "4. Ռուսաց լեզու", "5. Տեխնոլոգիա"],
        "saturday": ["Այս օրը դասեր նախատեսված չեն:"]
    },
    "5-Բ": {
        "monday": ["1. Մաթեմատիկա", "2. Մայրենի", "3. Ռուսաց լեզու", "4. Բնագիտություն", "5. Ֆիզկուլտուրա"],
        "tuesday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Օտար լեզու", "4. Հայրենագիտություն", "5. Երաժշտություն"],
        "wednesday": ["1. Մաթեմատիկա", "2. Մայրենի", "3. Կերպարվեստ", "4. Ռուսաց լեզու", "5. Տեխնոլոգիա"],
        "thursday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Օտար լեզու", "4. Բնագիտություն", "5. Ֆիզկուլտուրա"],
        "friday": ["1. Մաթեմատիկա", "2. Մայրենի", "3. Ռուսաց լեզու", "4. Հայրենագիտություն", "5. Տեխնոլոգիա"],
        "saturday": ["Այս օրը դասեր նախատեսված չեն:"]
    },
    "5-Գ": {
        "monday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Օտար լեզու", "4. Հայրենագիտություն", "5. Ֆիզկուլտուրա"],
        "tuesday": ["1. Մաթեմատիկա", "2. Մայրենի", "3. Բնագիտություն", "4. Ռուսաց լեզու", "5. Տեխնոլոգիա"],
        "wednesday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Օտար լեզու", "4. Կերպարվեստ", "5. Երաժշտություն"],
        "thursday": ["1. Մաթեմատիկա", "2. Մայրենի", "3. Հայրենագիտություն", "4. Ռուսաց լեզու", "5. Ֆիզկուլտուրա"],
        "friday": ["1. Մայրենի", "2. Մաթեմատիկա", "3. Բնագիտություն", "4. Ռուսաց լեզու", "5. Տեխնոլոգիա"],
        "saturday": ["Այս օրը դասեր նախատեսված չեն:"]
    },
    "6-Ա": {
        "monday": ["1. Հայոց լեզու", "2. Մաթեմատիկա", "3. Պատմություն", "4. Ռուսաց լեզու", "5. Ֆիզկուլտուրա"],
        "tuesday": ["1. Գրականություն", "2. Մաթեմատիկա", "3. Բնագիտություն", "4. Օտար լեզու", "5. Աշխարհագրություն"],
        "wednesday": ["1. Հայոց լեզու", "2. Մաթեմատիկա", "3. Ռուսաց լեզու", "4. Ինֆորմատիկա", "5. Երաժշտություն"],
        "thursday": ["1. Գրականություն", "2. Մաթեմատիկա", "3. Պատմություն", "4. Օտար լեզու", "5. Կերպարվեստ"],
        "friday": ["1. Հայոց լեզու", "2. Մաթեմատիկա", "3. Աշխարհագրություն", "4. Բնագիտություն", "5. Տեխնոլոգիա"],
        "saturday": ["Այս օրը դասեր նախատեսված չեն:"]
    },
    "6-Բ": {
        "monday": ["1. Մաթեմատիկա", "2. Հայոց լեզու", "3. Ռուսաց լեզու", "4. Պատմություն", "5. Ֆիզկուլտուրա"],
        "tuesday": ["1. Մաթեմատիկա", "2. Գրականություն", "3. Օտար լեզու", "4. Բնագիտություն", "5. Աշխարհագրություն"],
        "wednesday": ["1. Մաթեմատիկա", "2. Հայոց լեզու", "3. Ինֆորմատիկա", "4. Ռուսաց լեզու", "5. Կերպարվեստ"],
        "thursday": ["1. Մաթեմատիկա", "2. Գրականություն", "3. Օտար լեզու", "4. Պատմություն", "5. Երաժշտություն"],
        "friday": ["1. Մաթեմատիկա", "2. Հայոց լեզու", "3. Բնագիտություն", "4. Աշխարհագրություն", "5. Տեխնոլոգիա"],
        "saturday": ["Այս օրը դասեր նախատեսված չեն:"]
    },
    "6-Գ": {
        "monday": ["1. Հայոց լեզու", "2. Մաթեմատիկա", "3. Աշխարհագրություն", "4. Օտար լեզու", "5. Ֆիզկուլտուրա"],
        "tuesday": ["1. Գրականություն", "2. Մաթեմատիկա", "3. Պատմություն", "4. Ռուսաց լեզու", "5. Բնագիտություն"],
        "wednesday": ["1. Հայոց լեզու", "2. Մաթեմատիկա", "3. Օտար լեզու", "4. Երաժշտություն", "5. Ինֆորմատիկա"],
        "thursday": ["1. Գրականություն", "2. Մաթեմատիկա", "3. Ռուսաց լեզու", "4. Աշխարհագրություն", "5. Կերպարվեստ"],
        "friday": ["1. Հայոց լեզու", "2. Մաթեմատիկա", "3. Պատմություն", "4. Բնագիտություն", "5. Տեխնոլոգիա"],
        "saturday": ["Այս օրը դասեր նախատեսված չեն:"]
    },
    "7-Ա": {
        "monday": ["1. Հայոց լեզու", "2. Հանրահաշիվ", "3. Ֆիզիկա", "4. Պատմություն", "5. Օտար լեզու"],
        "tuesday": ["1. Գրականություն", "2. Երկրաչափություն", "3. Քիմիա", "4. Ռուսաց լեզու", "5. Ֆիզկուլտուրա"],
        "wednesday": ["1. Հանրահաշիվ", "2. Կենսաբանություն", "3. Պատմություն", "4. Ռուսաց լեզու", "5. Ինֆորմատիկա"],
        "thursday": ["1. Երկրաչափություն", "2. Հայոց լեզու", "3. Աշխարհագրություն", "4. Ֆիզիկա", "5. Օտար լեզու"],
        "friday": ["1. Գրականություն", "2. Հանրահաշիվ", "3. Կենսաբանություն", "4. Քիմիա", "5. Աշխարհագրություն"],
        "saturday": ["Այս օրը դասեր նախատեսված չեն:"]
    },
    "7-Բ": {
        "monday": ["1. Հանրահաշիվ", "2. Հայոց լեզու", "3. Պատմություն", "4. Ֆիզիկա", "5. Ռուսաց լեզու"],
        "tuesday": ["1. Երկրաչափություն", "2. Գրականություն", "3. Օտար լեզու", "4. Քիմիա", "5. Ֆիզկուլտուրա"],
        "wednesday": ["1. Հայոց լեզու", "2. Հանրահաշիվ", "3. Ինֆորմատիկա", "4. Կենսաբանություն", "5. Պատմություն"],
        "thursday": ["1. Գրականություն", "2. Երկրաչափություն", "3. Ֆիզիկա", "4. Աշխարհագրություն", "5. Ռուսաց լեզու"],
        "friday": ["1. Հանրահաշիվ", "2. Քիմիա", "3. Օտար լեզու", "4. Աշխարհագրություն", "5. Կենսաբանություն"],
        "saturday": ["Այս օրը դասեր նախատեսված չեն:"]
    },
    "7-Գ": {
        "monday": ["1. Ֆիզիկա", "2. Հանրահաշիվ", "3. Հայոց լեզու", "4. Օտար լեզու", "5. Պատմություն"],
        "tuesday": ["1. Քիմիա", "2. Երկրաչափություն", "3. Գրականություն", "4. Ֆիզկուլտուրա", "5. Ռուսաց լեզու"],
        "wednesday": ["1. Կենսաբանություն", "2. Հանրահաշիվ", "3. Ռուսաց լեզու", "4. Պատմություն", "5. Ինֆորմատիկա"],
        "thursday": ["1. Աշխարհագրություն", "2. Հայոց լեզու", "3. Երկրաչափություն", "4. Օտար լեզու", "5. Ֆիզիկա"],
        "friday": ["1. Հանրահաշիվ", "2. Գրականություն", "3. Աշխարհագրություն", "4. Կենսաբանություն", "5. Քիմիա"],
        "saturday": ["Այս օրը դասեր նախատեսված չեն:"]
    },
    "8-Ա": {
        "monday": ["1. Հայոց լեզու", "2. Հանրահաշիվ", "3. Ֆիզիկա", "4. Պատմություն", "5. Օտար լեզու"],
        "tuesday": ["1. Գրականություն", "2. Երկրաչափություն", "3. Քիմիա", "4. Հասարակագիտություն", "5. Ֆիզկուլտուրա"],
        "wednesday": ["1. Հանրահաշիվ", "2. Կենսաբանություն", "3. Պատմություն", "4. Ռուսաց լեզու", "5. Ինֆորմատիկա"],
        "thursday": ["1. Երկրաչափություն", "2. Հայոց լեզու", "3. Աշխարհագրություն", "4. Ֆիզիկա", "5. Օտար լեզու"],
        "friday": ["1. Գրականություն", "2. Պատմություն", "3. Կենսաբանություն", "4. Քիմիա", "5. ՆԶՊ"],
        "saturday": ["Այս օրը դասեր նախատեսված չեն:"]
    },
    "8-Բ": {
        "monday": ["1. Հանրահաշիվ", "2. Հայոց լեզու", "3. Պատմություն", "4. Ֆիզիկա", "5. Ռուսաց լեզու"],
        "tuesday": ["1. Երկրաչափություն", "2. Գրականություն", "3. Օտար լեզու", "4. Քիմիա", "5. ՆԶՊ"],
        "wednesday": ["1. Հայոց լեզու", "2. Հանրահաշիվ", "3. Հասարակագիտություն", "4. Կենսաբանություն", "5. Ինֆորմատիկա"],
        "thursday": ["1. Գրականություն", "2. Երկրաչափություն", "3. Ֆիզիկա", "4. Աշխարհագրություն", "5. Ֆիզկուլտուրա"],
        "friday": ["1. Հանրահաշիվ", "2. Պատմություն", "3. Օտար լեզու", "4. Քիմիա", "5. Կենսաբանություն"],
        "saturday": ["Այս օրը դասեր նախատեսված չեն:"]
    },
    "8-Գ": {
        "monday": ["1. Պատմություն", "2. Հանրահաշիվ", "3. Հայոց լեզու", "4. Օտար լեզու", "5. Ֆիզիկա"],
        "tuesday": ["1. Քիմիա", "2. Երկրաչափություն", "3. Գրականություն", "4. Ռուսաց լեզու", "5. Ֆիզկուլտուրա"],
        "wednesday": ["1. Կենսաբանություն", "2. Հանրահաշիվ", "3. Ինֆորմատիկա", "4. Պատմություն", "5. Հասարակագիտություն"],
        "thursday": ["1. Աշխարհագրություն", "2. Հայոց լեզու", "3. Երկրաչափություն", "4. Ֆիզիկա", "5. Ռուսաց լեզու"],
        "friday": ["1. Գրականություն", "2. Հանրահաշիվ", "3. ՆԶՊ", "4. Օտար լեզու", "5. Քիմիա"],
        "saturday": ["Այս օրը դասեր նախատեսված չեն:"]
    },
    "9-Ա": {
        "monday": ["1. Հայոց լեզու", "2. Հանրահաշիվ", "3. Ֆիզիկա", "4. Հայոց պատմություն", "5. Օտար լեզու"],
        "tuesday": ["1. Գրականություն", "2. Երկրաչափություն", "3. Քիմիա", "4. Անգլերեն", "5. Ֆիզկուլտուրա"],
        "wednesday": ["1. Հանրահաշիվ", "2. Կենսաբանություն", "3. Համաշխարհային պատմություն", "4. Ռուսաց լեզու", "5. Ինֆորմատիկա"],
        "thursday": ["1. Երկրաչափություն", "2. Հայոց լեզու", "3. Աշխարհագրություն", "4. Ֆիզիկա", "5. Օտար լեզու"],
        "friday": ["1. Գրականություն", "2. Հայոց պատմություն", "3. Կենսաբանություն", "4. Հասարակագիտություն", "5. ՆԶՊ"],
        "saturday": ["Այս օրը դասեր նախատեսված չեն:"]
    },
    "9-Բ": {
        "monday": ["1. Հանրահաշիվ", "2. Հայոց լեզու", "3. Հայոց պատմություն", "4. Ֆիզիկա", "5. Ռուսաց լեզու"],
        "tuesday": ["1. Երկրաչափություն", "2. Գրականություն", "3. Օտար լեզու", "4. Քիմիա", "5. ՆԶՊ"],
        "wednesday": ["1. Հայոց լեզու", "2. Հանրահաշիվ", "3. Ինֆորմատիկա", "4. Կենսաբանություն", "5. Հասարակագիտություն"],
        "thursday": ["1. Գրականություն", "2. Երկրաչափություն", "3. Ֆիզիկա", "4. Աշխարհագրություն", "5. Ֆիզկուլտուրա"],
        "friday": ["1. Հանրահաշիվ", "2. Համաշխարհային պատմություն", "3. Օտար լեզու", "4. Քիմիա", "5. Կենսաբանություն"],
        "saturday": ["Այս օրը դասեր նախատեսված չեն:"]
    },
    "9-Գ": {
        "monday": ["1. Ֆիզիկա", "2. Հանրահաշիվ", "3. Հայոց լեզու", "4. Օտար լեզու", "5. Հայոց պատմություն"],
        "tuesday": ["1. Քիմիա", "2. Երկրաչափություն", "3. Գրականություն", "4. Ռուսաց լեզու", "5. Ֆիզկուլտուրա"],
        "wednesday": ["1. Կենսաբանություն", "2. Հանրահաշիվ", "3. Հասարակագիտություն", "4. Համաշխարհային պատմություն", "5. Ինֆորմատիկա"],
        "thursday": ["1. Աշխարհագրություն", "2. Հայոց լեզու", "3. Երկրաչափություն", "4. Օտար լեզու", "5. Ֆիզիկա"],
        "friday": ["1. Գրականություն", "2. Հանրահաշիվ", "3. ՆԶՊ", "4. Ռուսաց լեզու", "5. Քիմիա"],
        "saturday": ["Այս օրը դասեր նախատեսված չեն:"]
    }
}

DAYS_NAMES = {
    "monday": "Երկուշաբթի",
    "tuesday": "Երեքշաբթի",
    "wednesday": "Չորեքշաբթի",
    "thursday": "Հինգշաբթի",
    "friday": "Ուրբաթ",
    "saturday": "Շաբաթ"
}


# --- Запрос к Gemini API через aiohttp (без лишних библиотек) ---
async def get_ai_motivation(grade_num: int, grade_let: str) -> str:
    if not GEMINI_API_KEY:
        return "⚠️ ԱԲ բանալին (GEMINI_API_KEY) կարգավորված չէ:"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    
    # Берем список предметов этого класса для контекста
    class_key = f"{grade_num}-{grade_let}"
    class_schedule = SCHEDULE.get(class_key, {})
    subjects = set()
    for day_lessons in class_schedule.values():
        for lesson in day_lessons:
            if "." in lesson:
                subjects.add(lesson.split(".", 1)[1].strip())
    subjects_str = ", ".join(subjects) if subjects else "դպրոցական առարկաներ"

    prompt = (
        f"Դու ընկերասեր և ոգեշնչող դպրոցական օգնական ես: "
        f"Գրիր կարճ (2-3 նախադասություն), ջերմ ու մոտիվացնող հաղորդագրություն {grade_num}-րդ դասարանի աշակերտի համար: "
        f"Նրա առարկաներից են՝ {subjects_str}: "
        f"Պատմիր մեկ զվարճալի կամ զարմանալի փաստ այս առարկաներից մեկի մասին և քաջալերիր նրան լավ սովորել: "
        f"Պատասխանիր միայն հայերեն լեզվով և օգտագործիր էմոջիներ:"
    )

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        async with ClientSession() as session:
            async with session.post(url, json=payload, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    return "⚠️ ԱԲ-ն այս պահին զբաղված է, փորձեք մի փոքր ուշ:"
    except Exception:
        return "⚠️ Հնարավոր չեղավ կապ հաստատել ԱԲ-ի հետ:"


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
    rows = []
    current_row = []
    for num in range(1, 10):
        current_row.append(InlineKeyboardButton(text=f"{num}-րդ", callback_data=f"grade_num:{num}"))
        if len(current_row) == 3:
            rows.append(current_row)
            current_row = []
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_grade_letters_kb() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="Ա", callback_data="grade_let:Ա"),
            InlineKeyboardButton(text="Բ", callback_data="grade_let:Բ"),
            InlineKeyboardButton(text="Գ", callback_data="grade_let:Գ")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_days_kb() -> InlineKeyboardMarkup:
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
            InlineKeyboardButton(text="✨ Խորհուրդ ԱԲ-ից", callback_data="ai_motivate")
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
async def handle_day_selection(call: CallbackQuery, state: FSMContext):
    day_key = call.data.split(":")[1]
    user_grade = await get_user_grade(call.from_user.id)
    
    if not user_grade:
        await state.set_state(SetupGrade.grade_number)
        await call.message.edit_text(
            "Դասարանը ընտրված չէ: Խնդրում ենք ընտրել դասարանը:",
            reply_markup=get_grade_numbers_kb()
        )
        await call.answer()
        return

    grade_num, grade_let = user_grade
    grade_key = f"{grade_num}-{grade_let}"
    day_title = DAYS_NAMES.get(day_key, "")
    
    class_schedule = SCHEDULE.get(grade_key, {})
    lessons = class_schedule.get(day_key, ["Դասացուցակը դեռ լրացված չէ:"])
    schedule_text = "\n".join(lessons)

    text = (
        f"Դասարան՝ {grade_key}\n"
        f"Օր՝ {day_title}\n\n"
        f"Դասացուցակ՝\n{schedule_text}\n\n"
        "Ընտրեք այլ օր կամ փոխեք դասարանը:"
    )

    try:
        await call.message.edit_text(text, reply_markup=get_days_kb())
    except TelegramBadRequest:
        pass
    await call.answer()

@dp.callback_query(F.data == "ai_motivate")
async def handle_ai_motivate(call: CallbackQuery, state: FSMContext):
    user_grade = await get_user_grade(call.from_user.id)
    
    if not user_grade:
        await state.set_state(SetupGrade.grade_number)
        await call.message.edit_text(
            "Դասարանը ընտրված չէ: Խնդրում ենք ընտրել դասարանը:",
            reply_markup=get_grade_numbers_kb()
        )
        await call.answer()
        return

    grade_num, grade_let = user_grade
    await call.answer("✨ ԱԲ-ն մտածում է...")

    # Вызываем Gemini API
    ai_text = await get_ai_motivation(grade_num, grade_let)

    text = (
        f"🎓 Դասարան՝ {grade_num}-{grade_let}\n\n"
        f"💡 **ԱԲ-ի խորհուրդը քեզ համար.**\n{ai_text}\n\n"
        "Ընտրեք շաբաթվա օրը դասացուցակը տեսնելու համար:"
    )

    try:
        await call.message.edit_text(text, reply_markup=get_days_kb())
    except TelegramBadRequest:
        pass

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
