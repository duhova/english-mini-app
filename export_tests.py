import sqlite3
import json
import os

def export_tests():
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT level, question, option_a, option_b, option_c, correct, hint, explanation FROM tests")
    rows = cursor.fetchall()

    tests_by_level = {"Начальный": [], "Средний": [], "Продвинутый": []}

    for level, q, opt_a, opt_b, opt_c, correct, hint, expl in rows:
        correct_idx = correct - 1  # обратно в 0,1,2
        test_data = {
            "question": q,
            "options": [opt_a, opt_b, opt_c],
            "correct": correct_idx,
            "hint": hint,
            "explanation": expl
        }
        tests_by_level[level].append(test_data)

    os.makedirs('mini_app', exist_ok=True)
    with open('mini_app/tests.json', 'w', encoding='utf-8') as f:
        json.dump(tests_by_level, f, ensure_ascii=False, indent=2)

    print("✅ tests.json создан с подсказками и объяснениями")

if __name__ == "__main__":
    export_tests()