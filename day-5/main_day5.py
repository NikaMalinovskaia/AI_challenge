import time
import os
from litellm import completion, completion_cost

# Настройка параметров из окружения (передаются из run.sh)
API_BASE = os.getenv("LITELLM_API_BASE", "https://api.litellm.ai")
API_KEY = os.getenv("LITELLM_API_KEY")

# Четкое распределение моделей по уровням (слабая, средняя, сильная)
MODELS = {
    "Слабая модель (Light)": os.getenv("MODEL_WEAK", "huggingface/google/gemma-2-2b-it"),
    "Средняя модель (Standard)": os.getenv("MODEL_MEDIUM", "huggingface/mistralai/Mistral-7B-Instruct-v0.3"),
    "Сильная модель (Strong)": os.getenv("MODEL_STRONG", "huggingface/meta-llama/Meta-Llama-3-70B-Instruct")
}

def run_model_comparison(prompt: str):
    results = []
    
    print(f"🎯 Тестовый промпт для всех моделей:\n> «{prompt}»\n" + "-"*50)
    
    for tier, model_name in MODELS.items():
        print(f"🔄 Отправка запроса на [{tier}] -> `{model_name}`...")
        messages = [{"role": "user", "content": prompt}]
        
        start_time = time.perf_counter()
        try:
            # Один и тот же вызов через LiteLLM для каждой модели
            response = completion(
                model=model_name,
                messages=messages,
                temperature=0.7,
                api_base=API_BASE,
                api_key=API_KEY
            )
            end_time = time.perf_counter()
            elapsed_time = round(end_time - start_time, 3)
            
            # Сбор метрик (токены и стоимость)
            usage = response.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)
            
            cost = completion_cost(completion_response=response)
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
            print(f"   ✅ Успешно! Время: {elapsed_time}с | Токенов: {total_tokens} | Стоимость: ${cost:.6f}\n")
            
        except Exception as e:
            print(f"   ❌ Ошибка при запросе к {model_name}: {str(e)}\n")
            results.append({
                "tier": tier,
                "model": model_name,
                "error": str(e),
                "status": "Ошибка"
            })
            
    return results

def save_reports(prompt: str, results: list):
    # 1. Технический отчет с метриками (day5_metrics_report.md)
    tech_report = f"# 📊 Технический отчет: День 5 (Версии моделей)\n\n"
    tech_report += f"**Общий промпт:** `{prompt}`\n\n"
    tech_report += "| Уровень | Модель | Время (с) | Токены (Вх / Вых / Всего) | Стоимость ($) | Статус |\n"
    tech_report += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
    
    for r in results:
        if r["status"] == "Успешно":
            tokens_str = f"{r['prompt_tokens']} / {r['completion_tokens']} ({r['total_tokens']})"
            tech_report += f"| **{r['tier']}** | `{r['model']}` | {r['time']} | {tokens_str} | ${r['cost']:.6f} | ✅ |\n"
        else:
            tech_report += f"| **{r['tier']}** | `{r['model']}` | - | - | - | ❌ |\n"
            
    with open("day5_metrics_report.md", "w", encoding="utf-8") as f:
        f.write(tech_report)

    # 2. Итоговый файл со сравнением (answer_comparison.md)
    summary = f"# ⚖️ Сравнение моделей: Скорость, Ресурсы, Качество (День 5)\n\n"
    summary += f"**Исходный запрос:** `{prompt}`\n\n"
    
    summary += "## 🚀 1. Скорость\n"
    for r in results:
        if r["status"] == "Успешно":
            summary += f"* **{r['tier']}** (`{r['model']}`): **{r['time']} сек.**\n"
            
    summary += "\n## 💾 2. Ресурсоёмкость и стоимость\n"
    for r in results:
        if r["status"] == "Успешно":
            summary += f"* **{r['tier']}** — Токены: `{r['total_tokens']}` (Вх: {r['prompt_tokens']}, Вых: {r['completion_tokens']}), Стоимость: **${r['cost']:.6f}**\n"
            
    summary += "\n## 🧠 3. Качество ответов\n"
    for r in results:
        if r["status"] == "Успешно":
            snippet = r['content'][:300].replace('\n', ' ')
            summary += f"* **{r['tier']}** (`{r['model']}`):\n  > *«{snippet}...»*\n\n"
            
    summary += "## 💡 Итоговый вывод\n"
    summary += "Слабые модели (начало списка HF) обеспечивают мгновенный отклик и минимальные затраты, но подходят только для базовых задач. Средние модели (середина HF) держат отличный баланс скорости и качества. Сильные модели (конец/флагманы HF) требуют больше времени и ресурсов, но незаменимы для глубокого анализа.\n\n"
    summary += "### Полезные ссылки\n"
    summary += "* [Hugging Face Models Hub](https://huggingface.co/models)\n"
    summary += "* [Документация LiteLLM](https://docs.litellm.ai/)\n"

    with open("answer_comparison.md", "w", encoding="utf-8") as f:
        f.write(summary)
    
    print("📁 Отчеты успешно сохранены: `day5_metrics_report.md` и `answer_comparison.md`")

if __name__ == "__main__":
    test_prompt = "Объясни концепцию квантовых вычислений простыми словами для новичка."
    print("🚀 Запуск эксперимента Дня 5...\n" + "="*50)
    res = run_model_comparison(test_prompt)
    save_reports(test_prompt, res)
