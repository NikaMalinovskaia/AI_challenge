import requests
import json
import time

# Конфигурация локального эндпоинта Ollama
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5"

def query_local_llm(prompt: str):
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    
    start_time = time.time()
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        duration = time.time() - start_time
        
        if response.status_code == 200:
            return response.json().get("response", "").strip(), duration
        else:
            return f"Ошибка API: {response.status_code} - {response.text}", duration
    except Exception as e:
            duration = time.time() - start_time
            return f"Ошибка подключения к локальному серверу Ollama: {e}", duration

if __name__ == "__main__":
    print(f"=== Тестирование локальной LLM ({MODEL_NAME}) с замером производительности ===\n")

    test_cases = [
        ("Простой запрос (Smoke test)", "Привет! Назови язык программирования, для которого мы пишем систему код-ревью, в одном слове."),
        ("Запрос средней сложности (C# ООП)", "Объясни в двух предложениях, почему в C# рекомендуется использовать private поля и public свойства."),
        ("Сложный запрос (Анализ дефектов кода)", "Найди архитектурный дефект ООП в этом коде на C#: 'public class Account { public decimal balance; }' и предложи исправленный вариант.")
    ]

    for title, prompt in test_cases:
        print(f"🔹 {title}:")
        print(f"Промпт: {prompt}")
        
        answer, duration = query_local_llm(prompt)
        
        print(f"Ответ:\n{answer}")
        print(f"⏱ Время генерации: {duration:.2f} сек.\n" + "-"*40)
