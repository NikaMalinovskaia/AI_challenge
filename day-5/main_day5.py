import time
import os
from litellm import completion, completion_cost

# Конфигурация моделей из переменных окружения или значений по умолчанию
API_BASE = os.getenv("LITELLM_API_BASE", "https://api.litellm.ai")
API_KEY = os.getenv("LITELLM_API_KEY")
MODEL_WEAK = os.getenv("MODEL_WEAK", "deepseek/deepseek-chat")
MODEL_MEDIUM = os.getenv("MODEL_MEDIUM", "deepseek/deepseek-chat")
MODEL_STRONG = os.getenv("MODEL_STRONG", "deepseek/deepseek-reasoner")

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
            response = completion(
                model=model_name,
                messages=messages,
                temperature=0.7,
                api_base=API_BASE,
                api_key=API_KEY
            )
            end_time = time.perf_counter()
            elapsed_time = round(end_time - start_time, 3)
            
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
            print(f"   ✅ Готово за {elapsed_time}с | Токенов: {total_tokens} | Стоимость: ${cost:.6f}")
            
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
    # 1. Технический отчет с метриками
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

    # 2. Итоговый файл со сравнением (качество, скорость, ресурсоёмкость)
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
    summary += "Слабые модели оптимальны для простых задач из-за высокой скорости и минимальной стоимости. Средние модели обеспечивают сбалансированный результат, а сильные модели незаменимы для сложных логических цепочек, несмотря на большее время ответа и расход ресурсов.\n\n"
    summary += "### Полезные ссылки\n"
    summary += "* [Документация LiteLLM](https://docs.litellm.ai/)\n"
    summary += "* [Hugging Face Models Hub](https://huggingface.co/models)\n"

    with open("answer_comparison.md", "w", encoding="utf-8") as f:
        f.write(summary)
    
    print("\n📁 Отчеты успешно сохранены: `day5_metrics_report.md` и `answer_comparison.md`")

if __name__ == "__main__":
    test_prompt = "Объясни концепцию квантовых вычислений простыми словами для новичка."
    print("🚀 Запуск эксперимента Дня 5...\n" + "-"*50)
    res = run_model_comparison(test_prompt)
    save_reports(test_prompt, res)
