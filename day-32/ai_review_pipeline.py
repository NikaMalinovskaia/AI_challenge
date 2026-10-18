import os
import subprocess
import sys
from openai import OpenAI

MAX_DIFF_CHARS = 60_000


def get_git_diff():
    try:
        subprocess.run(
            ["git", "fetch", "origin", "main"],
            check=False,
            timeout=30,
            capture_output=True,
        )
        diff = subprocess.check_output(
            ["git", "diff", "origin/main...HEAD"],
            text=True,
            timeout=30,
        )
        return diff.strip()
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Не удалось получить diff с origin/main: {e}", file=sys.stderr)
        try:
            diff = subprocess.check_output(
                ["git", "diff", "HEAD~1"],
                text=True,
                timeout=30,
            )
            return diff.strip()
        except subprocess.CalledProcessError as inner_e:
            print(f"❌ Ошибка получения fallback diff: {inner_e}", file=sys.stderr)
            return ""
    except Exception as e:
        print(f"❌ Непредвиденная ошибка при выполнении git diff: {e}", file=sys.stderr)
        return ""


def generate_ai_review(diff_text):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Переменная окружения OPENAI_API_KEY не задана")

    base_url = os.getenv("OPENAI_BASE_URL", "https://llm.effective.land/v1")
    model_name = os.getenv("OPENAI_MODEL", "glm-5.3-flash")

    if len(diff_text) > MAX_DIFF_CHARS:
        diff_text = (
            diff_text[:MAX_DIFF_CHARS]
            + "\n\n# ... [Внимание: git diff был автоматически обрезан из-за превышения размера]"
        )

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    system_prompt = """
Ты — старший архитектор и Python-разработчик. Проведи AI Code Review для git diff с учётом правил проекта.

Правила разработки проекта (RAG Context):
1. Запрещены сырые SQL-запросы в бизнес-логике. Запросы должны проходить через паттерн Repository.
2. Использование параметров при формировании SQL-запросов (защита от SQL-инъекций).
3. Любые подключения к БД или внешним ресурсам должны оборачиваться в try/finally или контекстные менеджеры (with) для гарантированного закрытия соединений.
4. В коде не должно быть тестовых отладочных принтов или временных комментариев в ветке main.

Структура ответа (на русском языке):
1. 🎯 Общее резюме изменений
2. 🐛 Потенциальные баги и уязвимости
3. 🏗 Архитектурные проблемы и Code Smells
4. 💡 Рекомендации по улучшению
"""

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Вот git diff для анализа:\n\n```diff\n{diff_text}\n```",
                },
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Ошибка при вызове LLM API: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    print("🔍 Запуск AI Code Review Pipeline...")
    diff = get_git_diff()

    if not diff:
        print("⚠️ Изменения в git diff не обнаружены.")
        return

    print("📄 Git diff получен. Отправка в LLM...")
    review_result = generate_ai_review(diff)

    print("\n" + "=" * 50)
    print("🤖 РЕЗУЛЬТАТ AI CODE REVIEW:")
    print("=" * 50 + "\n")
    print(review_result)
    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
