import sqlite3
import json
import os

def get_hint(question):
    """Возвращает короткую подсказку на основе текста вопроса."""
    q = question.lower()
    if "to school every day" in q:
        return "Present Simple для she/he/it"
    elif "coffee every morning" in q:
        return "Present Simple с I"
    elif "homework now" in q or "tv now" in q or "picture now" in q or "english now" in q or "soccer now" in q:
        return "Действие происходит сейчас (Present Continuous)"
    elif "umbrella" in q or "orange" in q or "apple" in q:
        return "Перед гласным звуком используем 'an'"
    elif "tomato" in q or "baby" in q or "cat" in q or "dog" in q or "mouse" in q or "child" in q:
        return "Множественное число"
    elif "always" in q or "usually" in q or "every day" in q or "on sundays" in q:
        return "Present Simple"
    elif "present perfect" in q or "since 2018" in q or "since morning" in q:
        return "Present Perfect"
    elif "past continuous" in q or "when i called" in q or "when i arrived" in q:
        return "Past Continuous"
    elif "reported speech" in q or "he said" in q:
        return "Косвенная речь – согласование времён"
    elif "if i" in q and "would have" in q:
        return "Третье условное (нереальное прошлое)"
    elif "if i" in q and "would" in q:
        return "Второе условное (нереальное настоящее)"
    elif "by the time" in q:
        return "Past Perfect"
    elif "inversion" in q or "rarely" in q or "not only" in q or "hardly" in q:
        return "Инверсия после отрицательных наречий"
    elif "cleft sentence" in q or "it was" in q:
        return "Эмфатическая конструкция (cleft sentence)"
    else:
        return ""

def get_explanation(question, correct):
    """Генерирует подробное объяснение."""
    q = question.lower()
    # Определяем букву правильного ответа (A, B, C)
    if isinstance(correct, int):
        correct_letter = {1: 'A', 2: 'B', 3: 'C'}.get(correct, '?')
    else:
        correct_letter = correct.upper() if len(str(correct)) == 1 else '?'

    # Базовые объяснения
    if "to school every day" in q:
        return f"Вариант {correct_letter} правильный, так как для he/she/it в Present Simple используется окончание -s"
    elif "coffee every morning" in q:
        return f"Вариант {correct_letter} правильный, так как для I/you/we/they в Present Simple не используется окончание -s"
    elif "homework now" in q or "tv now" in q or "picture now" in q or "english now" in q or "soccer now" in q:
        return f"Вариант {correct_letter} правильный, так как для действий в момент речи используется Present Continuous (am/is/are + V-ing)"
    elif "umbrella" in q or "orange" in q or "apple" in q:
        return f"Вариант {correct_letter} правильный, так как перед гласным звуком используется неопределённый артикль 'an'"
    elif "tomato" in q or "baby" in q or "cat" in q:
        if "tomato" in q:
            return f"Вариант {correct_letter} правильный, так как слова на -o образуют множественное число с -es"
        elif "baby" in q:
            return f"Вариант {correct_letter} правильный, так как слова на -y после согласной меняют y на ies"
        else:
            return f"Вариант {correct_letter} правильный, множественное число образуется добавлением -s"
    elif "mouse" in q:
        return f"Вариант {correct_letter} правильный, так как 'mouse' во множественном числе — 'mice'"
    elif "child" in q:
        return f"Вариант {correct_letter} правильный, так как 'child' во множественном числе — 'children'"
    elif "present perfect" in q or "since 2018" in q or "since morning" in q:
        return f"Вариант {correct_letter} правильный, так как Present Perfect используется для действий, начавшихся в прошлом и продолжающихся до настоящего"
    elif "past continuous" in q or "when i called" in q or "when i arrived" in q:
        return f"Вариант {correct_letter} правильный, так как Past Continuous (was/were + V-ing) описывает длительное действие в прошлом, прерванное другим действием"
    elif "reported speech" in q or "he said" in q:
        return f"Вариант {correct_letter} правильный, так как в косвенной речи время и модальные глаголы сдвигаются назад"
    elif "if i" in q and "would have" in q:
        return f"Вариант {correct_letter} правильный, так как третье условное (If + Past Perfect, would have + V3) описывает нереальное прошлое"
    elif "if i" in q and "would" in q and "had" not in q:
        return f"Вариант {correct_letter} правильный, так как второе условное (If + Past Simple, would + V) описывает нереальное настоящее"
    elif "by the time" in q:
        return f"Вариант {correct_letter} правильный, так как Past Perfect показывает действие, завершённое до другого момента в прошлом"
    elif "inversion" in q or "rarely" in q or "not only" in q or "hardly" in q:
        return f"Вариант {correct_letter} правильный, так как после отрицательных наречий используется инверсия (вспомогательный глагол + подлежащее)"
    elif "cleft sentence" in q or "it was" in q:
        return f"Вариант {correct_letter} правильный, так как в эмфатических конструкциях (it is/was … that/who) выделяется важная часть предложения"
    else:
        return f"Правильный ответ: {correct_letter}. Обратите внимание на грамматическое правило."

def export_tests():
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    try:
        # Пытаемся получить все поля, включая hint и explanation (если они есть)
        cursor.execute("PRAGMA table_info(tests)")
        columns = [col[1] for col in cursor.fetchall()]
        has_hint = 'hint' in columns
        has_explanation = 'explanation' in columns

        if has_hint and has_explanation:
            cursor.execute("SELECT level, question, option_a, option_b, option_c, correct, hint, explanation FROM tests")
        else:
            cursor.execute("SELECT level, question, option_a, option_b, option_c, correct FROM tests")
    except sqlite3.OperationalError:
        print("Таблица tests не найдена в bot.db!")
        return

    rows = cursor.fetchall()
    tests_by_level = {"Начальный": [], "Средний": [], "Продвинутый": []}

    for row in rows:
        level = row[0]
        question = row[1]
        opt_a, opt_b, opt_c = row[2], row[3], row[4]
        correct = row[5]

        # correct в базе 1,2,3 → индекс 0,1,2
        correct_idx = correct - 1

        # Подсказка и объяснение
        if has_hint and has_explanation:
            hint = row[6] if row[6] else get_hint(question)
            explanation = row[7] if row[7] else get_explanation(question, correct)
        else:
            hint = get_hint(question)
            explanation = get_explanation(question, correct)

        test_data = {
            "question": question,
            "options": [opt_a, opt_b, opt_c],
            "correct": correct_idx,
            "hint": hint,
            "explanation": explanation
        }
        tests_by_level[level].append(test_data)

    # Создаём папку
    os.makedirs('mini_app', exist_ok=True)

    # Сохраняем JSON
    with open('mini_app/tests.json', 'w', encoding='utf-8') as f:
        json.dump(tests_by_level, f, ensure_ascii=False, indent=2)

    print("✅ Экспорт завершён:")
    for level, tests in tests_by_level.items():
        print(f"   {level}: {len(tests)} тестов")
    print("Файл сохранён: mini_app/tests.json")
    conn.close()

if __name__ == "__main__":
    export_tests()
