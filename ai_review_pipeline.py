import os
import subprocess
import sys
from openai import OpenAI

MAX_DIFF_CHARS = 50_000


def get_git_diff() -> str:
    base = "origin/main"
    try:
        subprocess.run(
            ["git", "fetch", "origin", "main"],
            check=True,
            timeout=30,
            capture_output=True,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"⚠️ Не удалось выполнить git fetch для origin/main: {e}", file=sys.stderr)
        base = "HEAD~1"

    try:
        return subprocess.check_output(
            ["git", "diff", f"{base}...HEAD"],
            text=True,
            timeout=30,
        ).strip()
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Ошибка получения diff с базой {base}, пробую HEAD~1", file=sys.stderr)
        try:
            return subprocess.check_output(
                ["git", "diff", "HEAD~1"],
                text=True,
                timeout=30,
            ).strip()
        except subprocess.CalledProcessError as inner_e:
            print(f"❌ Критическая ошибка получения git diff: {inner_e}", file=sys.stderr)
            return ""


def generate_ai_review(diff_text):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Переменная окружения OPENAI_API_KEY не задана")

    base_url = os.getenv("LLM_BASE_URL", "https://llm.effective.land/v1")
    model_name = os.getenv("LLM_MODEL", "glm-5.3-flash")

    if len(diff_text) > MAX_DIFF_CHARS:
        diff_text = (
            diff_text[:MAX_DIFF_CHARS]
            + "\n\n# ... [Diff truncated due to size limits]"
        )

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    system_prompt = """Ты — старший архитектор и Python-разработчик. Проведи AI Code Review для git diff с учётом стандартов и правил проекта.

Правила разработки проекта (RAG Context):
1. Запрещены сырые SQL-запросы в бизнес-логике. Используйте паттерн Repository.
2. Все SQL-запросы должны быть параметризованы для защиты от SQL-инъекций.
3. Соединения с базами данных и внешними ресурсами должны обязательно закрываться с использованием try/finally или контекстных менеджеров (with).
4. В коде не должно быть тестовых отладочных принтов или временных комментариев.

Ответ дай на русском языке по структуре:
1. 🎯 Общее резюме изменений
2. 🐛 Потенциальные баги и уязвимости
3. 🏗 Архитектурные проблемы и Code Smells
4. 💡 Рекомендации по улучшению"""

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
            timeout=60,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Ошибка при запросе к LLM API: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    print("🔍 Запуск AI Code Review Pipeline...", file=sys.stderr)
    diff = get_git_diff()

    if not diff:
        print("⚠️ Изменения в git diff не обнаружены.", file=sys.stderr)
        sys.exit(0)

    print(f"📄 Git diff получен (символов: {len(diff)}). Отправка в LLM...", file=sys.stderr)
    review_result = generate_ai_review(diff)

    print("\n" + "=" * 50)
    print("🤖 РЕЗУЛЬТАТ AI CODE REVIEW:")
    print("=" * 50 + "\n")
    print(review_result)
    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
