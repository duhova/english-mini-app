import sqlite3
import json


def export_tests():
    # Подключаемся к базе тестов
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    # Получаем все тесты
    cursor.execute("SELECT level, question, option_a, option_b, option_c, correct FROM tests")
    tests = cursor.fetchall()

    # Группируем по уровням
    tests_by_level = {
        "Начальный": [],
        "Средний": [],
        "Продвинутый": []
    }

    for level, question, opt_a, opt_b, opt_c, correct in tests:
        test_data = {
            "question": question,
            "options": [opt_a, opt_b, opt_c],
            "correct": ord(correct) - 65 if len(correct) == 1 else 0,  # A=0, B=1, C=2
            "explanation": get_explanation(question, correct)  # Добавим объяснения
        }
        tests_by_level[level].append(test_data)

    # Сохраняем в JSON
    with open('mini_app/tests.json', 'w', encoding='utf-8') as f:
        json.dump(tests_by_level, f, ensure_ascii=False, indent=2)

    print(f"Экспортировано тестов:")
    print(f"  Начальный: {len(tests_by_level['Начальный'])}")
    print(f"  Средний: {len(tests_by_level['Средний'])}")
    print(f"  Продвинутый: {len(tests_by_level['Продвинутый'])}")
    print("Файл tests.json создан в папке mini_app")

    conn.close()


def get_explanation(question, correct):
    """Генерируем объяснение на основе вопроса"""
    correct_letter = correct
    explanations = {
        'A': 'Первый вариант правильный',
        'B': 'Второй вариант правильный',
        'C': 'Третий вариант правильный'
    }

    # Базовые объяснения по типам вопросов
    if "to school every day" in question:
        return f"Вариант {correct_letter} правильный, так как для he/she/it в Present Simple используется окончание -s"
    elif "coffee every morning" in question:
        return f"Вариант {correct_letter} правильный, так как для I/you/we/they в Present Simple не используется окончание -s"
    elif "homework now" in question:
        return f"Вариант {correct_letter} правильный, так как для действий в момент речи используется Present Continuous (am/is/are + V-ing)"

    return f"Правильный ответ: {correct_letter}. {explanations.get(correct_letter, '')}"


if __name__ == "__main__":
    export_tests()