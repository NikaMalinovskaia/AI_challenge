import os
import subprocess
import sys
from openai import OpenAI

def get_git_diff():
    try:
        subprocess.run(["git", "fetch", "origin", "main"], check=False)
        diff = subprocess.check_output(
            ["git", "diff", "origin/main...HEAD"], 
            text=True
        )
        return diff.strip()
    except Exception as e:
        try:
            diff = subprocess.check_output(["git", "diff", "HEAD~1"], text=True)
            return diff.strip()
        except Exception as inner_e:
            print(f"Ошибка получения diff: {e} / {inner_e}")
            return ""

def generate_ai_review(diff_text):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Ошибка: OPENAI_API_KEY не задан.")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    system_prompt = """
Ты — старший архитектор и Python-разработчик. Проведи AI Code Review для git diff.
Ответ дай на русском языке по структуре:
1. 🎯 Общее резюме изменений
2. 🐛 Потенциальные баги и уязвимости
3. 🏗 Архитектурные проблемы и Code Smells
4. 💡 Рекомендации по улучшению
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Вот git diff:\n\n```diff\n{diff_text}\n```"}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content

def main():
    print("🔍 Запуск AI Code Review Pipeline...")
    diff = get_git_diff()
    
    if not diff:
        print("⚠️ Нет изменений в git diff.")
        return

    print("📄 Git diff получен. Отправка в OpenAI...")
    review_result = generate_ai_review(diff)
    
    print("\n" + "="*50)
    print("🤖 РЕЗУЛЬТАТ AI CODE REVIEW:")
    print("="*50 + "\n")
    print(review_result)
    print("\n" + "="*50)

if __name__ == "__main__":
    main()
