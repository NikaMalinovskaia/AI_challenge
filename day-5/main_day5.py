import time
import os
import sys
from litellm import completion, completion_cost

# Корректная конфигурация базового URL для корпоративного шлюза
API_BASE = os.getenv("LITELLM_API_BASE", "https://llm.effective.land/v1")
API_KEY = os.getenv("LITELLM_API_KEY")

# Названия моделей, доступных на вашем шлюзе
MODEL_WEAK = os.getenv("MODEL_WEAK", "gpt-4o-mini")
MODEL_MEDIUM = os.getenv("MODEL_MEDIUM", "gpt-4o")
MODEL_STRONG = os.getenv("MODEL_STRONG", "gpt-4o") # или пропишите сильную модель из вашего шлюза

MODELS = {
    "Слабая модель (Light)": MODEL_WEAK,
    "Средняя модель (Standard)": MODEL_MEDIUM,
    "Сильная модель (Reasoning)": MODEL_STRONG
}

def run_model_comparison(prompt: str):
    results = []
    
    for tier, model_name in MODELS.items():
        print(f"🔄 Отправка запроса на [{tier}] ({model_name})...")
        messages = [{"role": "user", "content": prompt}]
        
        start_time = time.perf_counter()
        try:
            # Передаем custom_llm_provider="openai" для корректной работы LiteLLM Proxy
            response = completion(
                model=model_name,
                messages=messages,
                temperature=0.7,
                api_base=API_BASE,
                api_key=API_KEY,
                custom_llm_provider="openai"
            )
            end_time = time.perf_counter()
            elapsed_time = round(end_time - start_time, 3)
            
            usage = response.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)
            
            try:
                cost = completion_cost(completion_response=response)
            except Exception:
                cost = 0.0  # Кастомные прокси могут не возвращать прайсинг
                
            content = response.choices[0].message.content
            
            results.append({
                "tier": tier,
                "model": model_name,
                "time": elapsed_time,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "cost": cost,
                "content": content,
                "status": "Успешно"
            })
            print(f"   ✅ Готово за {elapsed_time}с | Токенов: {total_tokens}")
            
        except Exception as e:
            print(f"   ❌ Ошибка: {str(e)}")
            results.append({
                "tier": tier,
                "model": model_name,
                "error": str(e),
                "status": "Ошибка"
            })
            
    return results

def save_reports(prompt: str, results: list):
    # Проверяем, есть ли хотя бы один успешный ответ
    successful = [r for r in results if r["status"] == "Успешно"]
    if not successful:
        print("\n❌ Ни одна модель не вернула успешный ответ! Отчеты не будут созданы.")
        sys.exit(1) # Завершаем скрипт с кодом ошибки для run.sh

    # 1. Технический отчет
    tech_report = f"# 📊 Технический отчет: День 5 (Версии моделей)\n\n"
    tech_report += f"**Промпт:** `{prompt}`\n\n"
    tech_report += "| Уровень | Модель | Время (с) | Токены (Вх/Вых/Всего) | Стоимость ($) | Статус |\n"
    tech_report += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
    
    for r in results:
        if r["status"] == "Успешно":
            tokens_str = f"{r['prompt_tokens']} / {r['completion_tokens']} ({r['total_tokens']})"
            tech_report += f"| **{r['tier']}** | `{r['model']}` | {r['time']} | {tokens_str} | ${r['cost']:.6f} | ✅ |\n"
        else:
            tech_report += f"| **{r['tier']}** | `{r['model']}` | - | - | - | ❌ |\n"
            
    with open("day5_metrics_report.md", "w", encoding="utf-8") as f:
        f.write(tech_report)

    # 2. Итоговый файл со сравнением
    summary = f"# ⚖️ Сравнение моделей: Скорость, Ресурсы, Качество (День 5)\n\n"
    summary += f"**Задача:** `{prompt}`\n\n"
    
    summary += "## 🚀 Скорость отклика\n"
    for r in results:
        if r["status"] == "Успешно":
            summary += f"* **{r['tier']}** (`{r['model']}`): **{r['time']} сек.**\n"
            
    summary += "\n## 💾 Ресурсоёмкость и стоимость\n"
    for r in results:
        if r["status"] == "Успешно":
            summary += f"* **{r['tier']}** — Токены: `{r['total_tokens']}`, Стоимость: **${r['cost']:.6f}**\n"
            
    summary += "\n## 🧠 Качество ответов\n"
    for r in results:
        if r["status"] == "Успешно":
            snippet = r['content'][:250].replace('\n', ' ')
            summary += f"* **{r['tier']}**:\n  > *«{snippet}...»*\n\n"
            
    summary += "## 💡 Итоговый вывод\n"
    summary += "Слабые модели оптимальны для простых задач из-за высокой скорости. Сильные модели обеспечивают высокую точность в сложных логических задачах.\n\n"

    with open("answer_comparison.md", "w", encoding="utf-8") as f:
        f.write(summary)
    
    print("\n📁 Отчеты успешно сохранены: `day5_metrics_report.md` и `answer_comparison.md`")

if __name__ == "__main__":
    test_prompt = "Объясни концепцию квантовых вычислений простыми словами для новичка."
    print("🚀 Запуск эксперимента Дня 5...\n" + "-"*50)
    res = run_model_comparison(test_prompt)
    save_reports(test_prompt, res)
