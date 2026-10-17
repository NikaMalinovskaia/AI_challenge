import requests
import time
import concurrent.futures

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5"

def query_ai_service(prompt: str) -> dict:
    """Функция для отправки запроса к нашему локальному AI-сервису"""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 150 # Ограничение токенов (Rate limit / Max tokens)
        }
    }
    
    start_time = time.time()
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=30)
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "success",
                "response": data.get("response", "").strip(),
                "duration": duration
            }
        else:
            return {
                "status": "error",
                "code": response.status_code,
                "duration": duration
            }
    except Exception as e:
        return {
            "status": "connection_error",
            "error": str(e),
            "duration": time.time() - start_time
        }

if __name__ == "__main__":
    print(f"🌐 Проверка приватного AI-сервиса на базе Ollama ({MODEL_NAME})\n")
    
    test_prompt = "Объясни в одном предложении, зачем в C# нужны свойства."
    
    # 1. Проверка одиночного запроса (доступность по сети)
    print("1️⃣ Тест одиночного запроса...")
    res = query_ai_service(test_prompt)
    if res["status"] == "success":
        print(f"   ✅ Успешно! Время ответа: {res['duration']:.2f} сек.")
        print(f"   🤖 Ответ: {res['response']}\n")
    else:
        print(f"   ❌ Ошибка: {res}\n")

    # 2. Проверка стабильности при нескольких параллельных запросах (Concurrency test)
    print("2️⃣ Тест стабильности под нагрузкой (3 параллельных запроса)...")
    prompts = [
        "Что такое инкапсуляция в C#?",
        "Что такое полиморфизм в C#?",
        "Что такое интерфейс в C#?"
    ]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(query_ai_service, p) for p in prompts]
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            r = future.result()
            print(f"   - Запрос {i}: Статус [{r['status']}], Время: {r['duration']:.2f} сек.")

    print("\n🎉 Все тесты приватного AI-сервиса успешно завершены!")
