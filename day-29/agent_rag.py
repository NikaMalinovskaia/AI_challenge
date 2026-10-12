import requests
import time

class LocalRAGAgent:
    def __init__(self, model_name: str = "qwen2.5", temperature: float = 0.2, max_tokens: int = 500):
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.local_model = model_name
        self.ollama_url = "http://localhost:11434/api/generate"
        
        # База знаний
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
        
        self.reset_memory()

    def local_retrieval(self, query: str) -> list:
        query_lower = query.lower()
        scored_docs = []
        for doc in self.knowledge_base:
            score = sum(1 for word in query_lower.split() if word in doc["content"].lower() or word in doc["topic"].lower())
            scored_docs.append((score, doc))
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        top_docs = [doc for score, doc in scored_docs if score > 0]
        return top_docs if top_docs else [self.knowledge_base[0]]

    def chat_single(self, user_message: str, prompt_template_type: str = "Стандартный", custom_temp: float = None, custom_max_tokens: int = None) -> tuple:
        start_time = time.time()
        
        temp = custom_temp if custom_temp is not None else self.temperature
        tokens = custom_max_tokens if custom_max_tokens is not None else self.max_tokens
        
        retrieved_docs = self.local_retrieval(user_message)
        context_text = "\n\n".join([f"Источник [{d['id']}]: {d['content']}" for d in retrieved_docs])
        
        # Четкое разделение поведения и тона для каждой роли
        if prompt_template_type == "Строгий код-ревьюер":
            system_instructions = (
                "Роль: Ты — беспощадный техлид и строгий код-ревьюер. "
                "Пиши предельно коротко, без вводных слов и приветствий. Выписывай ошибки строго по пунктам и давай исправленный код.\n"
                "ОТВЕЧАЙ СТРОГО НА РУССКОМ ЯЗЫКЕ. ЗАПРЕЩЕНО ИСПОЛЬЗОВАТЬ ИЕРОГЛИФЫ.\n\n"
            )
            user_prompt = (
                f"Контекст: {context_text}\n\n"
                f"Код на ревью:\n{user_message}\n\n"
                "Сделай жесткий разбор нарушений ООП в этом коде."
            )
        elif prompt_template_type == "Преподаватель-наставник":
            system_instructions = (
                "Роль: Ты — добрый и понятливый преподаватель университета. "
                "Объясняй концепции через жизненные аналогии, поддерживай студента и давай развернутые пояснения.\n"
                "ОТВЕЧАЙ СТРОГО НА РУССКОМ ЯЗЫКЕ. ЗАПРЕЩЕНО ИСПОЛЬЗОВАТЬ ИЕРОГЛИФЫ.\n\n"
            )
            user_prompt = (
                f"Контекст: {context_text}\n\n"
                f"Вопрос студента:\n{user_message}\n\n"
                "Объясни тему подробно, просто и доступно."
            )
        else:
            system_instructions = (
                "Роль: Ты — технический справочник по C#. Отвечай сухо, четко и информативно.\n"
                "ОТВЕЧАЙ СТРОГО НА РУССКОМ ЯЗЫКЕ. ЗАПРЕЩЕНО ИСПОЛЬЗОВАТЬ ИЕРОГЛИФЫ.\n\n"
            )
            user_prompt = (
                f"Контекст: {context_text}\n\n"
                f"Запрос:\n{user_message}"
            )
            
        full_prompt = system_instructions + user_prompt
        
        self.history.append({"role": "user", "content": user_message})
        
        try:
            payload = {
                "model": self.local_model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temp,
                    "num_predict": tokens,
                    "num_ctx": 2048
                }
            }
            response = requests.post(self.ollama_url, json=payload, timeout=90)
            if response.status_code == 200:
                answer = response.json().get("response", "").strip()
            else:
                answer = f"Ошибка сервера Ollama: {response.status_code}"
                
            duration = time.time() - start_time
            self.history.append({"role": "assistant", "content": answer})
            return answer, retrieved_docs, duration
            
        except Exception as e:
            self.history.pop()
            raise Exception(f"Ошибка генерации: {e}")
            
    def reset_memory(self):
        self.history = []
