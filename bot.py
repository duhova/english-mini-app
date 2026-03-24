import aiosqlite
import os
import asyncio
import json
import random
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram import F

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8538737346:AAHRcw-saKM8HIvdNjduyj0y8Ikg7MV47JY"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ======================================================
# ЖИЗНИ ДЛЯ ГРАММАТИЧЕСКИХ ТЕСТОВ
# ======================================================
async def get_lives(user_id: int) -> int:
    """Получить текущее количество жизней пользователя"""
    async with aiosqlite.connect(TESTS_DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS user_lives (
            user_id INTEGER PRIMARY KEY,
            lives INTEGER DEFAULT 3
        )
        """)
        await db.commit()
        cursor = await db.execute("SELECT lives FROM user_lives WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
        if row:
            return row[0]
        else:
            # Добавляем пользователя с 3 жизнями
            await db.execute("INSERT INTO user_lives (user_id, lives) VALUES (?, ?)", (user_id, 3))
            await db.commit()
            return 3

async def decrease_life(user_id: int) -> int:
    """Уменьшить жизнь пользователя на 1 и вернуть оставшиеся жизни"""
    async with aiosqlite.connect(TESTS_DB) as db:
        lives = await get_lives(user_id)
        lives = max(lives - 1, 0)
        await db.execute("UPDATE user_lives SET lives=? WHERE user_id=?", (lives, user_id))
        await db.commit()
        return lives

async def reset_lives(user_id: int):
    """Сброс жизней пользователя до 3"""
    async with aiosqlite.connect(TESTS_DB) as db:
        await db.execute("UPDATE user_lives SET lives=3 WHERE user_id=?", (user_id,))
        await db.commit()

# ======================================================
# ЖИЗНИ ДЛЯ ТЕСТА НА ПЕРЕВОД СЛОВ
# ======================================================
async def get_word_lives(user_id: int) -> int:
    """Получить количество жизней для теста на перевод слов"""
    async with aiosqlite.connect(WORDS_DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS word_user_lives (
            user_id INTEGER PRIMARY KEY,
            lives INTEGER DEFAULT 3
        )
        """)
        # Таблица жизней пользователей
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_lives (
                user_id INTEGER PRIMARY KEY,
                lives INTEGER DEFAULT 3
            )
        ''')
        await db.commit()
        cursor = await db.execute("SELECT lives FROM word_user_lives WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
        if row:
            return row[0]
        else:
            await db.execute("INSERT INTO word_user_lives (user_id, lives) VALUES (?, ?)", (user_id, 3))
            await db.commit()
            return 3

async def get_word_lives(user_id: int) -> int:
    """Получение количества жизней пользователя"""
    async with aiosqlite.connect(WORDS_DB) as db:
        cursor = await db.execute("SELECT lives FROM user_lives WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
        if row is None:
            # Если пользователя нет, создаем с 3 жизнями
            await db.execute("INSERT INTO user_lives(user_id, lives) VALUES (?, ?)", (user_id, 3))
            await db.commit()
            return 3
        return row[0]

async def decrease_word_life(user_id: int) -> int:
    """Уменьшение жизни на 1, возвращает оставшиеся жизни"""
    lives = await get_word_lives(user_id)
    lives = max(0, lives - 1)
    async with aiosqlite.connect(WORDS_DB) as db:
        await db.execute(
            "INSERT INTO user_lives(user_id, lives) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET lives=?", (user_id, lives, lives)
        )
        await db.commit()
    return lives

async def reset_word_lives(user_id: int):
    """Сброс жизней до 3"""
    async with aiosqlite.connect(WORDS_DB) as db:
        await db.execute(
            "INSERT INTO user_lives(user_id, lives) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET lives=?", (user_id, 3, 3)
        )
        await db.commit()

# ======================================================
# КОМАНДА /lives
# ======================================================
@dp.message(Command("lives"))
async def show_lives(message: types.Message):
    try:
        user_id = message.from_user.id
        grammar_lives = await get_lives(user_id)
        word_lives = await get_word_lives(user_id)

        await message.answer(f"❤️ Жизни для грамматических тестов: {grammar_lives}\n"
                             f"📝 Жизни для перевода слов: {word_lives}")

        if grammar_lives == 0:
            await reset_lives(user_id)
            await message.answer("💡 Жизни для грамматики восстановлены до 3.")

        if word_lives == 0:
            await reset_word_lives(user_id)
            await message.answer("💡 Жизни для перевода слов восстановлены до 3.")

    except Exception as e:
        logger.error(f"Ошибка в /lives: {e}")
        await message.answer("Произошла ошибка.")
        
LEVELS = ["Начальный", "Средний", "Продвинутый"]


# FSM
class UserState(StatesGroup):
    learning_words = State()
    waiting_for_test_answer = State()
    grammar_select_level = State()
    grammar_waiting_answer = State()
    selecting_word_level = State()  # для выбора уровня слов
    selecting_mini_app_level = State()  # для выбора уровня мини-апп


# ======================================================
# КОНФИГУРАЦИЯ БАЗ ДАННЫХ
# ======================================================
WORDS_DB = "db.sqlite3"  # База со словами
TESTS_DB = "bot.db"  # База с тестами


async def init_databases():
    """Инициализация обеих баз данных"""
    try:
        # 1. Инициализация базы слов
        async with aiosqlite.connect(WORDS_DB) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL,
                    transcription TEXT,
                    translation TEXT NOT NULL,
                    example_en TEXT,
                    example_ru TEXT,
                    level TEXT
                )
            ''')

            await db.execute('''
                CREATE TABLE IF NOT EXISTS web_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    level TEXT,
                    score INTEGER,
                    total INTEGER,
                    ts DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.execute('''
            CREATE TABLE IF NOT EXISTS user_lives (
            user_id INTEGER PRIMARY KEY,
            lives INTEGER DEFAULT 3
                 )
            ''')
            await db.commit()
            logger.info(f"База слов {WORDS_DB} проверена")

            async def get_word_lives(user_id: int) -> int:
                """Получение количества жизней пользователя"""
                async with aiosqlite.connect(WORDS_DB) as db:
                    cursor = await db.execute("SELECT lives FROM user_lives WHERE user_id=?", (user_id,))
                    row = await cursor.fetchone()
                    if row is None:
                        # Если пользователя нет, создаем с 3 жизнями
                        await db.execute("INSERT INTO user_lives(user_id, lives) VALUES (?, ?)", (user_id, 3))
                        await db.commit()
                        return 3
                    return row[0]
        
            async def decrease_word_life(user_id: int) -> int:
                """Уменьшение жизни на 1, возвращает оставшиеся жизни"""
                lives = await get_word_lives(user_id)
                lives = max(0, lives - 1)
                async with aiosqlite.connect(WORDS_DB) as db:
                    await db.execute("INSERT INTO user_lives(user_id, lives) VALUES (?, ?) "
                                     "ON CONFLICT(user_id) DO UPDATE SET lives=?", (user_id, lives, lives))
                    await db.commit()
                return lives

            async def reset_word_lives(user_id: int):
                """Сброс жизней до 3"""
                async with aiosqlite.connect(WORDS_DB) as db:
                    await db.execute("INSERT INTO user_lives(user_id, lives) VALUES (?, ?) "
                                "ON CONFLICT(user_id) DO UPDATE SET lives=?", (user_id, 3, 3))
                    await db.commit()

        # 2. Проверка базы тестов
        async with aiosqlite.connect(TESTS_DB) as db:
            cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tests'")
            table_exists = await cursor.fetchone()

            if not table_exists:
                logger.warning(f"В базе {TESTS_DB} нет таблицы 'tests'. Запустите db_init.py")
            else:
                cursor = await db.execute("SELECT COUNT(*) FROM tests")
                count = await cursor.fetchone()
                logger.info(f"В базе тестов найдено {count[0]} тестов")

    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}")
        raise


async def get_random_word(level=None):
    """Получение случайного слова из базы данных"""
    try:
        # Проверяем существование файла базы
        if not os.path.exists(WORDS_DB):
            logger.error(f"Файл базы данных {WORDS_DB} не найден!")
            return None

        async with aiosqlite.connect(WORDS_DB) as db:
            # Проверяем существование таблицы
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='words'"
            )
            table_exists = await cursor.fetchone()

            if not table_exists:
                logger.error(f"Таблица 'words' не найдена в {WORDS_DB}")
                return None

            # Получаем слово
            if level and level in LEVELS:
                cursor = await db.execute(
                    "SELECT id, word, transcription, translation, example_english, example_russian, level FROM words WHERE level = ? ORDER BY RANDOM() LIMIT 1",
                    (level,)
                )
            else:
                cursor = await db.execute(
                    "SELECT id, word, transcription, translation, example_english, example_russian, level FROM words ORDER BY RANDOM() LIMIT 1"
                )

            row = await cursor.fetchone()

            if not row:
                logger.warning(f"Нет слов в базе для уровня: {level}")
                return None

            logger.info(f"Получено слово: {row[1]} (уровень: {row[6]})")
            return row

    except Exception as e:
        logger.error(f"Ошибка при получении слова: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

# ======================================================
# API ДЛЯ МИНИ-АПП (чтобы мини-апп получал тесты)
# ======================================================
async def get_tests_for_mini_app(level=None):
    """Получение тестов для мини-апп"""
    try:
        async with aiosqlite.connect(TESTS_DB) as db:
            if level:
                cursor = await db.execute(
                    "SELECT id, question, option_a, option_b, option_c, correct FROM tests WHERE level = ?",
                    (level,)
                )
            else:
                cursor = await db.execute(
                    "SELECT id, question, option_a, option_b, option_c, correct, level FROM tests"
                )
            tests_data = await cursor.fetchall()

            # Преобразуем в удобный формат
            result = []
            for test in tests_data:
                if level:
                    test_dict = {
                        "id": test[0],
                        "question": test[1],
                        "options": [test[2], test[3], test[4]],
                        "correct": test[5]
                    }
                else:
                    test_dict = {
                        "id": test[0],
                        "question": test[1],
                        "options": [test[2], test[3], test[4]],
                        "correct": test[5],
                        "level": test[6]
                    }
                result.append(test_dict)

            return result
    except Exception as e:
        logger.error(f"Ошибка при получении тестов: {e}")
        return []


# ======================================================
# START
# ======================================================
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    try:
        await state.clear()

        kb = [
            [types.KeyboardButton(text="Изучать слова")],
            [types.KeyboardButton(text="Грамматические тесты (в боте)")],
            [types.KeyboardButton(text="📱 Тесты в мини-приложении")]
        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

        await message.answer(
            "Привет! Я бот для изучения английского.\n\n"
            "Выбери действие:\n"
            "• Изучать слова - изучение слов с примерами\n"
            "• Грамматические тесты - тесты прямо в боте\n"
            "• Тесты в мини-приложении - интерактивные тесты в WebApp",
            reply_markup=keyboard
        )
        logger.info(f"Пользователь {message.from_user.id} начал работу с ботом")
    except Exception as e:
        logger.error(f"Ошибка в start: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")


# ======================================================
# UNIVERSAL BACK BUTTON (works ALWAYS)
# ======================================================
@dp.message(F.text == "Назад")
async def back_to_main(message: types.Message, state: FSMContext):
    try:
        await state.clear()

        kb = [
            [types.KeyboardButton(text="Изучать слова")],
            [types.KeyboardButton(text="Грамматические тесты (в боте)")],
            [types.KeyboardButton(text="📱 Тесты в мини-приложении")]
        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await message.answer("Главное меню:", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Ошибка в back_to_main: {e}")
        await message.answer("Произошла ошибка.")


# ======================================================
# WORD LEARNING (изучать слова)
# ======================================================
@dp.message(F.text == "Изучать слова")
async def learn_words(message: types.Message, state: FSMContext):
    try:
        kb = [[types.KeyboardButton(text=level)] for level in LEVELS]
        kb.append([types.KeyboardButton(text="Любой уровень")])
        kb.append([types.KeyboardButton(text="Назад")])

        user_id = message.from_user.id
        word_lives = await get_word_lives(user_id)  # Получаем жизни для слов

        await message.answer(
            f"Выберите уровень слов:\n\n❤️ Жизни для теста на перевод слов: {word_lives}",
            reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        )
        await state.set_state(UserState.selecting_word_level)
    except Exception as e:
        logger.error(f"Ошибка в learn_words: {e}")
        await message.answer("Произошла ошибка.")


# Выбор уровня для изучения слов
@dp.message(UserState.selecting_word_level, F.text.in_(LEVELS + ["Любой уровень"]))
async def select_word_level(message: types.Message, state: FSMContext):
    try:
        level = message.text if message.text != "Любой уровень" else None
        await state.update_data(selected_level=level)
        await state.set_state(UserState.learning_words)

        # Проверяем, есть ли слова для этого уровня
        word_data = await get_random_word(level)
        if not word_data:
            # Проверяем, есть ли вообще слова в базе
            async with aiosqlite.connect(WORDS_DB) as db:
                cursor = await db.execute("SELECT COUNT(*) FROM words")
                total_count = (await cursor.fetchone())[0]

                if total_count == 0:
                    await message.answer(
                        "❌ База данных слов пуста!\n\n"
                        "Запустите команду для добавления слов:\n"
                        "`python generate_words.py`"
                    )
                    await state.clear()
                    return
                elif level:
                    cursor = await db.execute("SELECT COUNT(*) FROM words WHERE level = ?", (level,))
                    level_count = (await cursor.fetchone())[0]

                    if level_count == 0:
                        await message.answer(
                            f"❌ Нет слов для уровня '{level}'.\n\n"
                            f"Всего слов в базе: {total_count}\n"
                            f"Доступные уровни можно проверить командой:\n"
                            "`python check_words.py`"
                        )
                        await state.clear()
                        return

            await message.answer(f"❌ Нет слов для уровня '{message.text}'. Попробуйте другой уровень.")
            return

        await show_word(message, state)

    except Exception as e:
        logger.error(f"Ошибка в select_word_level: {e}")
        await message.answer("Произошла ошибка при выборе уровня.")


async def show_word(message: types.Message, state: FSMContext):
    try:
        user_data = await state.get_data()
        level = user_data.get("selected_level")

        word_data = await get_random_word(level)
        if not word_data:
            await message.answer("Нет слов для этого уровня. Добавьте слова в базу данных.")
            return

        word_id, word, transcription, translation, example_en, example_ru, word_level = word_data

        await state.update_data(
            current_word=word,
            current_translation=translation,
            current_word_id=word_id
        )
        user_id = message.from_user.id
        word_lives = await get_word_lives(user_id)
        text = f"❤️ Жизни: {word_lives}\n\n" + text# добавляем сверху

        text = f"<b>Слово:</b> {word}\n"
        if transcription:
            text += f"<b>Транскрипция:</b> {transcription}\n"
        text += f"<b>Перевод:</b> {translation}\n"
        if example_en:
            text += f"<b>Пример:</b>\n{example_en}\n"
        if example_ru:
            text += f"{example_ru}"

        kb = [
            [types.KeyboardButton(text="Следующее слово")],
            [types.KeyboardButton(text="Тест на перевод")],
            [types.KeyboardButton(text="Назад")]
        ]

        await message.answer(text,
                             reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True),
                             parse_mode="HTML")
        logger.info(f"Показано слово пользователю {message.from_user.id}: {word}")
    except Exception as e:
        logger.error(f"Ошибка в show_word: {e}")
        await message.answer("Произошла ошибка.")

@dp.message(F.text == "Следующее слово")
async def next_word(message: types.Message, state: FSMContext):
    try:
        await show_word(message, state)
    except Exception as e:
        logger.error(f"Ошибка в next_word: {e}")
        await message.answer("Произошла ошибка.")


@dp.message(F.text == "Тест на перевод")
async def translation_test(message: types.Message, state: FSMContext):
    try:
        user_data = await state.get_data()
        word = user_data.get("current_word")
        correct_translation = user_data.get("current_translation")

        if not word or not correct_translation:
            await message.answer("Ошибка: не найдено текущее слово.")
            return

        # Генерируем неправильные варианты
        async with aiosqlite.connect(WORDS_DB) as db:
            cursor = await db.execute(
                "SELECT translation FROM words WHERE translation != ? ORDER BY RANDOM() LIMIT 3",
                (correct_translation,)
            )
            wrong = [row[0] for row in await cursor.fetchall()]

        while len(wrong) < 3:
            wrong.append("???")

        options = [correct_translation] + wrong
        random.shuffle(options)

        kb = [[types.KeyboardButton(text=o)] for o in options]

        await state.update_data(test_answer=correct_translation)
        await state.set_state(UserState.waiting_for_test_answer)

        await message.answer(
            f"Как переводится слово '{word}'?",
            reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        )
    except Exception as e:
        logger.error(f"Ошибка в translation_test: {e}")
        await message.answer("Произошла ошибка.")


@dp.message(UserState.waiting_for_test_answer)
async def check_test_answer(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        user_answer = message.text
        correct_answer = data.get("test_answer")
        user_id = message.from_user.id  # сохраняем ID пользователя

        if user_answer == correct_answer:
            await message.answer("✅ Правильно! Отличная работа!")
        else:
            # Уменьшаем жизнь
            lives_left = await decrease_word_life(user_id)
            if lives_left > 0:
                await message.answer(
                    f"❌ Неправильно. Правильный ответ: {correct_answer}\n"
                    f"❤️ Осталось жизней: {lives_left}"
                )
            else:
                await message.answer(
                    f"❌ Неправильно. Правильный ответ: {correct_answer}\n"
                    f"💀 У вас закончились жизни! Изучение слов остановлено."
                )
                await state.clear()
                return

        # Возвращаемся к изучению слов, если жизни ещё есть
        await state.set_state(UserState.learning_words)
        await state.update_data(test_answer=None)

        kb = [
            [types.KeyboardButton(text="Следующее слово")],
            [types.KeyboardButton(text="Тест на перевод")],
            [types.KeyboardButton(text="Назад")]
        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await message.answer("Что дальше?", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Ошибка в check_test_answer: {e}")
        await message.answer("Произошла ошибка.")


# ======================================================
# MINI-APP TESTS (WebApp)
# ======================================================
@dp.message(F.text == "📱 Тесты в мини-приложении")
async def mini_app_tests(message: types.Message, state: FSMContext):
    try:
        # Создаем клавиатуру с выбором уровня для мини-апп
        kb = [
            [types.KeyboardButton(text="Начальный уровень (мини-апп)")],
            [types.KeyboardButton(text="Средний уровень (мини-апп)")],
            [types.KeyboardButton(text="Продвинутый уровень (мини-апп)")],
            [types.KeyboardButton(text="Назад")]
        ]

        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

        await message.answer(
            "Выберите уровень тестов для мини-приложения:\n\n"
            "Мини-приложение откроется в Telegram и будет использовать тесты из базы данных.",
            reply_markup=keyboard
        )
        await state.set_state(UserState.selecting_mini_app_level)
    except Exception as e:
        logger.error(f"Ошибка в mini_app_tests: {e}")
        await message.answer("Произошла ошибка.")


# Выбор уровня для мини-апп
@dp.message(UserState.selecting_mini_app_level, F.text.endswith("(мини-апп)"))
async def select_mini_app_level(message: types.Message, state: FSMContext):
    try:
        # Извлекаем уровень из текста
        text = message.text
        if "Начальный" in text:
            level = "Начальный"
        elif "Средний" in text:
            level = "Средний"
        elif "Продвинутый" in text:
            level = "Продвинутый"
        else:
            level = "Начальный"

        # Получаем тесты для этого уровня
        tests = await get_tests_for_mini_app(level)

        if not tests:
            await message.answer(f"❌ Нет тестов для уровня '{level}' в базе данных.")
            return

        # Получаем user_id и lives
        user_id = message.from_user.id
        lives = await get_word_lives(user_id)  # функция из user_lives

        # Создаем объект для передачи в Mini-App
        webapp_data = {
            "user_id": user_id,
            "lives": lives,
            "level": level
        }

        # В Mini-App URL вставлять не обязательно, просто открываем URL
        web_app_url = "https://duhova.github.io/english-mini-app/"
        web_app = WebAppInfo(url=web_app_url)

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"📱 Открыть тесты ({level})",
                    web_app=web_app
                )]
            ]
        )

        # Отправляем сообщение пользователю с кнопкой
        await message.answer(
            f"✅ Найдено {len(tests)} тестов для уровня '{level}'.\n\n"
            "Нажмите кнопку ниже, чтобы открыть мини-приложение с тестами:",
            reply_markup=keyboard
        )

        logger.info(f"Пользователь {user_id} выбрал мини-апп уровень: {level}, тестов: {len(tests)}")

        # Очищаем состояние
        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка в select_mini_app_level: {e}")
        await message.answer("Произошла ошибка.")


# ======================================================
# WEBAPP RESULT HANDLER
# ======================================================
@dp.message(F.content_type == types.ContentType.WEB_APP_DATA)
async def handle_webapp_result(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)

        user_id = message.from_user.id
        level = data.get("level", "Неизвестно")
        score = data.get("score", 0)
        total = data.get("total", 0)

        # Сохраняем результат в базу слов
        async with aiosqlite.connect(WORDS_DB) as db:
            await db.execute(
                "INSERT INTO web_results (user_id, level, score, total) VALUES (?, ?, ?, ?)",
                (user_id, level, score, total)
            )
            await db.commit()

        # Отправляем результат пользователю
        percentage = (score / total * 100) if total > 0 else 0

        if percentage >= 80:
            emoji = "🎉"
            message_text = "Отличный результат!"
        elif percentage >= 60:
            emoji = "👍"
            message_text = "Хороший результат!"
        else:
            emoji = "📚"
            message_text = "Продолжайте учиться!"

        await message.answer(
            f"{emoji} <b>Результат теста</b>\n\n"
            f"🏆 Уровень: {level}\n"
            f"✅ Правильных: {score}/{total}\n"
            f"📊 Процент: {percentage:.1f}%\n\n"
            f"{message_text}\n\n"
            "Результат сохранён в вашу историю.",
            parse_mode="HTML"
        )

        logger.info(f"WebApp результат от {user_id}: {score}/{total} ({level}), {percentage:.1f}%")

    except Exception as e:
        logger.error(f"Ошибка в handle_webapp_result: {e}")
        await message.answer("❌ Ошибка обработки результата теста.")


# ======================================================
# ГРАММАТИЧЕСКИЕ ТЕСТЫ (в боте)
# ======================================================
@dp.message(F.text == "Грамматические тесты (в боте)")
async def grammar_tests_menu(message: types.Message, state: FSMContext):
    try:
        kb = [[types.KeyboardButton(text=level)] for level in LEVELS]
        kb.append([types.KeyboardButton(text="Назад")])
        await state.set_state(UserState.grammar_select_level)

        user_id = message.from_user.id
        grammar_lives = await get_lives(user_id)  # Получаем жизни для грамматики

        await message.answer(
            f"Выберите уровень грамматики:\n\n❤️ Жизни для грамматических тестов: {grammar_lives}",
            reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        )
    except Exception as e:
        logger.error(f"Ошибка в grammar_tests_menu: {e}")
        await message.answer("Произошла ошибка.")


@dp.message(UserState.grammar_select_level, F.text.in_(LEVELS))
async def grammar_start(message: types.Message, state: FSMContext):
    try:
        level = message.text
        await state.update_data(grammar_level=level)

        async with aiosqlite.connect(TESTS_DB) as db:
            cur = await db.execute(
                "SELECT id, question, option1, option2, option3, option4, answer FROM grammar_tests WHERE level=? ORDER BY RANDOM() LIMIT 1",
                (level,)
            )
            row = await cur.fetchone()

        if not row:
            await message.answer("Нет тестов для этого уровня.")
            return

        test_id, q, o1, o2, o3, o4, correct = row

        await state.update_data(
            current_test=row,
            correct_answer=correct
        )
        await state.set_state(UserState.grammar_waiting_answer)

        kb = [
            [types.KeyboardButton(text="1. " + o1)],
            [types.KeyboardButton(text="2. " + o2)],
            [types.KeyboardButton(text="3. " + o3)],
            [types.KeyboardButton(text="4. " + o4)],
            [types.KeyboardButton(text="Назад")]
        ]

        await message.answer(
            f"📝 {q}",
            reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        )
    except Exception as e:
        logger.error(f"Ошибка в grammar_start: {e}")
        await message.answer("Произошла ошибка.")


# ======================================================
# МОДИФИКАЦИЯ ГРАММАТИЧЕСКИХ ТЕСТОВ С УЧЕТОМ ЖИЗНЕЙ
# ======================================================
@dp.message(UserState.grammar_waiting_answer)
async def grammar_check(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        correct = data["correct_answer"]
        user_id = message.from_user.id

        if message.text.startswith(str(correct)):
            await message.answer("✅ Правильно! Отличная работа!")
        else:
            # Уменьшаем жизнь
            new_lives = await decrease_life(user_id)
            if new_lives > 0:
                await message.answer(f"❌ Неправильно! Правильный ответ: {correct}\n❤️ Осталось жизней: {new_lives}")
            else:
                await message.answer(f"❌ Неправильно! Правильный ответ: {correct}\n💀 У вас закончились жизни! Тест завершён.")
                await state.clear()
                return

        # Переходим к следующему вопросу
        await grammar_start(message, state)

    except Exception as e:
        logger.error(f"Ошибка в grammar_check: {e}")
        await message.answer("Произошла ошибка.")


# ======================================================
# RUN
# ======================================================
async def main():
    # Отладочная информация
    print("=== ЗАПУСК БОТА ===")
    print(f"База слов: {WORDS_DB} - {'существует' if os.path.exists(WORDS_DB) else 'НЕ НАЙДЕНА'}")
    print(f"База тестов: {TESTS_DB} - {'существует' if os.path.exists(TESTS_DB) else 'НЕ НАЙДЕНА'}")

    if os.path.exists(WORDS_DB):
        import sqlite3
        conn = sqlite3.connect(WORDS_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT level, COUNT(*) FROM words GROUP BY level")
        print("Слова в базе:")
        words_found = False
        for level, count in cursor.fetchall():
            print(f"  {level}: {count} слов")
            words_found = True
        if not words_found:
            print("  ❌ БАЗА ПУСТА! Запустите: python generate_words.py")
        conn.close()

    await init_databases()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())