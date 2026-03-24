# check_words.py
import sqlite3
from utils import check_answer, lose_life, add_coins, increment_streak

# Очередь неправильных вопросов для адаптивного повторения
wrong_queue = {}

def handle_answer(user_id, question_id, answer):
    """
    Обработка ответа пользователя:
    - Проверка правильности
    - Добавление в очередь повторов при ошибке
    - Потеря жизни / начисление монет и увеличение streak
    """
    correct = check_answer(question_id, answer)
    if not correct:
        wrong_queue.setdefault(user_id, []).append(question_id)
        lose_life(user_id)
        print(f"❌ Пользователь {user_id} ошибся. Вопрос {question_id} добавлен в очередь повторов.")
    else:
        add_coins(user_id, 5)
        increment_streak(user_id)
        if user_id in wrong_queue and question_id in wrong_queue[user_id]:
            wrong_queue[user_id].remove(question_id)
        print(f"✅ Пользователь {user_id} ответил правильно! +5 монет.")
    return correct

def check_tests():
    """
    Проверка таблицы tests и вывод статистики и примеров вопросов
    """
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    # Проверяем наличие таблицы tests
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tests'")
    if not cursor.fetchone():
        print("❌ Таблица 'tests' не найдена в базе bot.db!")
        conn.close()
        return

    # Статистика по уровням
    cursor.execute("SELECT level, COUNT(*) FROM tests GROUP BY level")
    print("📊 Статистика по тестам:")
    for level, count in cursor.fetchall():
        print(f"  {level}: {count} тестов")

    # Несколько примеров вопросов
    print("\n🔤 Примеры тестов:")
    cursor.execute("SELECT question, option_a, option_b, option_c, correct, level FROM tests LIMIT 10")
    for question, a, b, c, correct, level in cursor.fetchall():
        print(f"  [{level}] {question}")
        print(f"     A: {a}  B: {b}  C: {c}  ✅ Correct: {correct}")

    conn.close()

def get_adaptive_question(user_id):
    """
    Возвращает вопрос из очереди неправильных ответов, если есть
    """
    if user_id in wrong_queue and wrong_queue[user_id]:
        question_id = wrong_queue[user_id][0]  # берем первый вопрос
        return question_id
    return None

if __name__ == "__main__":
    check_tests()