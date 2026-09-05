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
        
        report += f"## Стратегия: {name}\n\n"
        report += f"**Промпт:** `{prompt_text}`\n\n"
        report += f"**Ответ модели:**\n{answer_text}\n\n---\n\n"
    except Exception as e:
        report += f"## Стратегия: {name}\n\nОшибка: {e}\n\n---\n\n"

with open("answer_comparison.md", "w", encoding="utf-8") as f:
    f.write(report)

print("Готово! Отчет сохранен в файл answer_comparison.md")
