import os
from openai import OpenAI

class LLMAgent:
    def __init__(self, model_name: str = "glm-5.3-flash", temperature: float = 0.7):
        self.model_name = model_name
        self.temperature = temperature
        
        # Возвращаем фоллбек для ключа, чтобы Streamlit работал без лишних настроек окружения
        api_key = os.environ.get("LITELLM_API_KEY") or "sk-L2Fx4Xsvy_OA6gcp3gG2pA"
        
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://llm.effective.land/v1",
        )
        
        # Агент снова хранит свою память внутри себя
        self.messages = [
            {"role": "system", "content": "Ты — умный и лаконичный AI-ассистент."}
        ]

    def chat(self, user_message: str) -> str:
        """Принимает запрос пользователя, сохраняет контекст и возвращает ответ."""
        self.messages.append({"role": "user", "content": user_message})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=self.messages,
                temperature=self.temperature,
            )
            answer = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": answer})
            return answer
            
        except Exception as e:
            # Если произошла ошибка (например, сеть отпала), удаляем последнее 
            # сообщение пользователя, чтобы не ломать контекст
            self.messages.pop()
            raise Exception(f"Ошибка API: {e}")
            
    def reset_memory(self):
        """Сбрасывает контекст диалога до начального состояния."""
        self.messages = [
            {"role": "system", "content": "Ты — умный и лаконичный AI-ассистент."}
        ]
