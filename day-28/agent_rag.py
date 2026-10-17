import os
import requests
import time
from openai import OpenAI

class LocalRAGAgent:
    def __init__(self, model_name: str = "qwen2.5", temperature: float = 0.7):
        self.temperature = temperature
        
        # Настройка облачного клиента с правильным ключом и моделью из Дня 6
        api_key = os.environ.get("LITELLM_API_KEY") or "sk-L2Fx4Xsvy_OA6gcp3gG2pA"
        self.cloud_client = OpenAI(
            api_key=api_key,
            base_url="https://llm.effective.land/v1",
        )
        # Возвращаем рабочее имя модели из вашего проверенного агента
        self.cloud_model = "glm-5.3-flash"
        
        # Настройка локальной Ollama
        self.ollama_url = "http://localhost:11434/api/generate"
        self.local_model = model_name
        
        # База знаний (индекс)
        self.knowledge_base = [
            {
                "id": "doc_1",
                "topic": "Инкапсуляция и свойства в C#",
                "content": "В C# поля класса должны быть private для защиты внутреннего состояния. Для доступа к ним используются public свойства (properties) с get и set accessor-ами."
            },
            {
                "id": "doc_2",
                "topic": "Наследование и полиморфизм",
                "content": "Для переопределения виртуального метода в C# используется ключевое слово override в дочернем классе, а в базовом метод должен быть virtual."
            },
            {
                "id": "doc_3",
                "topic": "Интерфейсы в C#",
                "content": "Интерфейсы определяют контракт поведения. Начиная с C# 8.0, интерфейсы могут содержать реализации методов по умолчанию (default interface methods)."
            }
        ]
        
        # Раздельная память для режимов
        self.histories = {
            "local": [{"role": "system", "content": "Ты — преподаватель по C# ООП. Отвечай на основе контекста."}],
            "cloud": [{"role": "system", "content": "Ты — преподаватель по C# ООП. Отвечай на основе контекста."}]
        }

    def local_retrieval(self, query: str) -> list:
        query_lower = query.lower()
        scored_docs = []
        for doc in self.knowledge_base:
            score = sum(1 for word in query_lower.split() if word in doc["content"].lower() or word in doc["topic"].lower())
            scored_docs.append((score, doc))
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        top_docs = [doc for score, doc in scored_docs if score > 0]
        return top_docs if top_docs else [self.knowledge_base[0]]

    def chat_single(self, user_message: str, mode: str) -> tuple:
        start_time = time.time()
        
        # 1. Локальный Retrieval для формирования RAG-контекста
        retrieved_docs = self.local_retrieval(user_message)
        context_text = "\n\n".join([f"Источник [{d['id']}]: {d['content']}" for d in retrieved_docs])
        
        rag_prompt = (
            f"Контекст из базы знаний:\n{context_text}\n\n"
            f"Вопрос пользователя: {user_message}\n\n"
            "Дай ответ, опираясь на контекст."
        )
        
        # Добавляем в историю
        self.histories[mode].append({"role": "user", "content": rag_prompt})
        answer = ""
        
        try:
            if mode == "local":
                payload = {
                    "model": self.local_model,
                    "prompt": rag_prompt,
                    "stream": False,
                    "options": {"temperature": self.temperature}
                }
                response = requests.post(self.ollama_url, json=payload, timeout=90)
                if response.status_code == 200:
                    answer = response.json().get("response", "").strip()
                else:
                    answer = f"Ошибка локального сервера Ollama: {response.status_code}"
            else:
                # Запрос к облачному API с правильной моделью
                response = self.cloud_client.chat.completions.create(
                    model=self.cloud_model,
                    messages=self.histories[mode],
                    temperature=self.temperature,
                )
                answer = response.choices[0].message.content
                
            duration = time.time() - start_time
            self.histories[mode].append({"role": "assistant", "content": answer})
            return answer, retrieved_docs, duration
            
        except Exception as e:
            self.histories[mode].pop()
            raise Exception(f"Ошибка генерации ({mode}): {e}")
            
    def reset_memory(self, mode: str = None):
        if mode:
            self.histories[mode] = [{"role": "system", "content": "Ты — преподаватель по C# ООП."}]
        else:
            for m in self.histories:
                self.histories[m] = [{"role": "system", "content": "Ты — преподаватель по C# ООП."}]
