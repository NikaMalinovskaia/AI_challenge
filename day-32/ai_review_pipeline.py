import os
import subprocess
import sys
from openai import OpenAI

def get_git_diff():
    """
    Получает diff изменений между текущей веткой и origin/main.
    В средах CI (GitHub Actions) fetch-depth должен быть равен 0 или содержать origin/main.
    """
    try:
        # Подтягиваем актуальное состояние ветки main для корректного сравнения
        subprocess.run(["git", "fetch", "origin", "main"], check=False)
        
        # Получаем diff относительно origin/main
        diff = subprocess.check_output(
            ["git", "diff", "origin/main...HEAD"], 
            text=True
        )
        return diff.strip()
    except Exception as e:
        # Резервный вариант, если fetch не сработал или нет origin/main
        try:
            diff = subprocess.check_output(
                ["git", "diff", "HEAD~1"], 
                text=True
            )
            return diff.strip()
        except Exception as inner_e:
            print(f"Ошибка при получении git diff: {e} / {inner_e}")
            return ""

def generate_ai_review(diff_text):
    """
    Отправляет diff в OpenAI API и получает структурированный ответ.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Ошибка: Переменная окружения OPENAI_API_KEY не задана.")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    system_prompt = """
Ты — старший Python/Fullstack разработчик и системный архитектор. 
Твоя задача — провести AI Code Review переданного `git diff`.

Подготовь структурированный отчет на русском языке по следующему шаблону:

### 🎯 Общее резюме изменений
(Кратко опиши, что было изменено/добавлено)

### 🐛 Потенциальные баги и уязвимости
(Ошибки логики, необработанные исключения, утечки ресурсов, проблемы безопасности)

### 🏗 Архитектурные проблемы и Code Smells
(Нарушение SOLID, плохая связность, дублирование кода, отсутствие модульности)

### 💡 Рекомендации по улучшению
(Оптимизация производительности, чистота кода, читаемость, типизация)

Будь точен, приведи конкретные строки и примеры исправлений, если находишь недочеты.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Вот git diff пулл-реквеста:\n\n```diff\n{diff_text}\n```"}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content

def main():
    print("🔍 Запуск AI Code Review Pipeline...")
    
    diff = get_git_diff()
    
    if not diff:
        print("⚠️ Нет изменений в git diff. Убедись, что пулл-реквест содержит отличия от ветки main.")
        return

    print("📄 Git diff успешно получен. Отправка в OpenAI...")
    
    review_result = generate_ai_review(diff)
    
    print("\n" + "="*50)
    print("🤖 РЕЗУЛЬТАТ AI CODE REVIEW пупупу:")
    print("="*50 + "\n")
    print(review_result)
    print("\n" + "="*50)

if __name__ == "__main__":
    main()
