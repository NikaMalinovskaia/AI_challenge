import os
from openai import OpenAI

class SimpleLLMAgent:
    """
    Простой агент, инкапсулирующий логику взаимодействия с LLM через API.
    """
    def __init__(self, model_name: str = "glm-4.7-flash"):
        self.model_name = model_name
        # Инициализация HTTP-клиента под корпоративный шлюз LiteLLM
        self.client = OpenAI(
            api_key=os.environ.get("LITELLM_API_KEY"),
            base_url="https://llm.effective.land/v1",
        )
        self.system_prompt = (
            "Ты — полезный и вежливый AI-ассистент. Отвечай четко, грамотно и по существу."
        )

    def run(self, user_query: str) -> str:
        """
        Принимает запрос пользователя, отправляет его в LLM и возвращает ответ.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Ошибка при обращении к агенту: {str(e)}"
