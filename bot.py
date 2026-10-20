import asyncio
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

# Токен берем из переменных окружения
TOKEN = os.getenv("BOT_TOKEN")
# Render автоматически передает номер порта в переменную PORT
PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Обработчики бота
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(f"Привет, {message.from_user.first_name}! Я работаю на Render в облаке 24/7.")

@dp.message()
async def echo(message: Message):
    await message.answer(f"Вы написали: {message.text}")

# Веб-страница для проверки работоспособности (Health check)
async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"Веб-сервер запущен на порту {PORT}")

async def main():
    if not TOKEN:
        raise ValueError("Ошибка: BOT_TOKEN не задан в переменных окружения!")

    # Запускаем одновременно веб-сервер и опрос Telegram
    await start_web_server()
    print("Бот начинает polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
