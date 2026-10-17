import os
import json
from openai import OpenAI

class LLMAgent:
    def __init__(self, model_name: str = "glm-4.7-flash", temperature: float = 0.7, storage_file: str = "chat_history.json"):
        self.model_name = model_name
        self.temperature = temperature
        self.storage_file = storage_file
        
        api_key = os.environ.get("LITELLM_API_KEY") or "sk-L2Fx4Xsvy_OA6gcp3gG2pA"
        
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://llm.effective.land/v1",
        )
        
        # Загружаем историю и проверяем, была ли она найдена на диске
        self.messages, self.loaded_from_disk = self._load_history()

    def _load_history(self) -> tuple[list, bool]:
        """Загружает историю диалога из JSON-файла. Возвращает историю и флаг успешной загрузки."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 1: # Больше 1, если есть что-то помимо системного промпта
                        return data, True
            except Exception:
                pass
                
        return [
            {"role": "system", "content": "Ты — умный и лаконичный AI-ассистент."}
        ], False

    def _save_history(self):
        """Сохраняет текущую историю диалога в JSON-файл."""
        try:
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(self.messages, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка при сохранении истории: {e}")

    def chat(self, user_message: str) -> str:
        """Принимает запрос, сохраняет в историю, отправляет в LLM и фиксирует результат."""
        self.messages.append({"role": "user", "content": user_message})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=self.messages,
                temperature=self.temperature,
            )
            answer = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": answer})
            
            self._save_history()
            return answer
            
        except Exception as e:
            self.messages.pop()
            raise Exception(f"Ошибка API: {e}")
            
    def reset_memory(self):
        """Сбрасывает контекст и удаляет файл сохранения."""
        self.messages = [
            {"role": "system", "content": "Ты — умный и лаконичный AI-ассистент."}
        ]
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except Exception:
                pass
