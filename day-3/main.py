import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["LITELLM_API_KEY"],
    base_url="https://llm.effective.land/v1",
)

MODEL_NAME = "<model>"  # Замените на вашу модель

task = (
    "Крестьянину нужно перевезти через реку волка, козу и капусту. У него есть лодка, "
    "в которую помещается только крестьянин, а с ним только один предмет (волк, коза или капуста). "
    "Волк ест козу, коза ест капусту, если оставить их без присмотра. Как перевезти всех?"
)

prompts = {
    "1. Прямой ответ": task,
    "2. Пошаговое решение": task + " Решай строго пошагово, описывая каждое действие.",
    "3. Мета-промпт": "Сначала составь максимально эффективный системный промпт для решения логической задачи о переправе, а затем примени его к следующей задаче: " + task,
    "4. Группа экспертов": "Рассмотри задачу с позиций трех экспертов: Логик (проверяет безопасность), Логистик (планирует рейсы) и Критик (ищет ошибки). Каждый высказывает мнение, после чего выносится итоговое решение. Задача: " + task
}

report = "# Сравнение стратегий промптинга\n\n"
report += f"**Исходная задача:** {task}\n\n---\n\n"

# Словарь для сохранения ответов (чтобы потом передать на анализ)
responses_storage = {}

for name, prompt_text in prompts.items():
    print(f"Выполняется стратегия: {name}...")
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Ты эксперт в решении логических задач."},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.3,
        )
        answer_text = response.choices[0].message.content
        responses_storage[name] = answer_text
        
        report += f"## Стратегия: {name}\n\n"
        report += f"**Промпт:** `{prompt_text}`\n\n"
        report += f"**Ответ модели:**\n{answer_text}\n\n---\n\n"
    except Exception as e:
        report += f"## Стратегия: {name}\n\nОшибка: {e}\n\n---\n\n"

# --- АВТОМАТИЧЕСКОЕ СРАВНЕНИЕ (Закрывает требования ТЗ) ---
print("Генерация выводов и сравнения...")
comparison_prompt = f"""
Проанализируй четыре ответа модели на задачу о переправе, полученные разными стратегиями промптинга.
Ответь на два вопроса в формате Markdown-списка:
1. **Отличаются ли ответы?** (Сравни их по структуре, глубине проработки и наличию доказательств).
2. **Какой способ дал наиболее точный и качественный результат?** (Обоснуй выбор).

Вот тексты ответов для анализа:
---
1. Прямой ответ:
{responses_storage.get('1. Прямой ответ', 'Нет данных')}

2. Пошаговое решение:
{responses_storage.get('2. Пошаговое решение', 'Нет данных')}

3. Мета-промпт:
{responses_storage.get('3. Мета-промпт', 'Нет данных')}

4. Группа экспертов:
{responses_storage.get('4. Группа экспертов', 'Нет данных')}
"""

try:
    comp_response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": comparison_prompt}],
        temperature=0.3,
    )
    report += "## Сравнение результатов и выводы\n\n"
    report += comp_response.choices[0].message.content + "\n"
except Exception as e:
    report += "## Сравнение результатов и выводы\n\nОшибка при генерации сравнения: " + str(e) + "\n"

# Сохраняем итоговый файл
with open("answer_comparison.md", "w", encoding="utf-8") as f:
    f.write(report)

print("Готово! Полный отчет (включая сравнение) сохранен в файл answer_comparison.md")
