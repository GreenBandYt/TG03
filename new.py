from config import TOKEN, GBt_key
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, FSInputFile
import sqlite3
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import aiohttp
import logging


bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

class Form(StatesGroup):
    name = State()
    age = State()
    city = State()

def init_db():
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        age INTEGER NOT NULL,
        city TEXT NOT NULL)
    ''')
    conn.commit()
    conn.close()

init_db()


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await message.answer("Привет! Как тебя зовут?")
    await state.set_state(Form.name)

@dp.message(Form.name)
async def name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Сколько тебе лет?")
    await state.set_state(Form.age)

@dp.message(Form.age)
async def age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("В каком городе ты проживаете?")
    await state.set_state(Form.city)

@dp.message(Form.city)
async def city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    user_data = await state.get_data()


    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, age, city) VALUES (?, ?, ?)", (user_data['name'], user_data['age'], user_data['city']))
    conn.commit()
    conn.close()
    await message.answer("Данные сохранены")

    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.openweathermap.org/data/2.5/weather?q={user_data['city']}&appid={GBt_key}&units=metric&lang=ru") as response:
            if response.status == 200:
                weather_data = await response.json()
                main = weather_data['main']
                weather = weather_data['weather'][0]
                #await message.answer(f"В городе {user_data['city']} сейчас {main['temp']} °C, {weather}.")
                temperature = main['temp']
                humidity = main['humidity']
                pressure = main['pressure']*0.750062
                wind_speed = weather_data['wind']['speed']
                await message.answer(f"Температура: {temperature} °C\nВлажность: {humidity}%\nДавление: {pressure} мм.рт.ст.\nСкорость ветра: {wind_speed} m/s")
                description = weather['description']

                weather_report = (f"В городе {user_data['city']},\n"
                                  f"сейчас {main['temp']} °C,\n"
                                  f"{description}.")
                await message.answer(weather_report)
            else:
                await message.answer("Произошла ошибка при получении данных о погоде.")

    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())