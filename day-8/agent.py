import os
import json
import time
from openai import OpenAI
import tiktoken

class TokenAgent:
    def __init__(self, model_name: str = "glm-4.7-flash", storage_dir: str = "chats_storage_day8"):
        self.model_name = model_name
        self.storage_dir = storage_dir
        self.last_attempt = None  # Сохраняем параметры последней попытки для сайдбара
        
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
            
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.encoding = None

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        if not self.encoding:
            return len(text.split()) * 2
        return len(self.encoding.encode(text))

    def count_messages_tokens(self, messages: list) -> int:
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            total += self.count_tokens(content) + 4
        return total

    def get_all_chats(self) -> dict:
        chats = {}
        if not os.path.exists(self.storage_dir):
            return chats
        for filename in os.listdir(self.storage_dir):
            if filename.endswith(".json"):
                chat_id = filename[:-5]
                filepath = os.path.join(self.storage_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        chats[chat_id] = {
                            "title": data.get("title", "Новый диалог"),
                            "messages": data.get("messages", [])
                        }
                except Exception:
                    pass
        return chats

    def create_new_chat(self) -> str:
        chat_id = str(int(time.time()))
        messages = [
            {"role": "system", "content": "Ты — полезный и лаконичный AI-ассистент."}
        ]
        self.save_chat(chat_id, "Новый диалог", messages)
        self.last_attempt = None
        return chat_id

    def load_chat(self, chat_id: str) -> list:
        filepath = os.path.join(self.storage_dir, f"{chat_id}.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("messages", [{"role": "system", "content": "Ты — полезный и лаконичный AI-ассистент."}])
            except Exception:
                pass
        return [{"role": "system", "content": "Ты — полезный и лаконичный AI-ассистент."}]

    def save_chat(self, chat_id: str, title: str, messages: list):
        filepath = os.path.join(self.storage_dir, f"{chat_id}.json")
        current_title = title
        if current_title == "Новый диалог":
            for msg in messages:
                if msg["role"] == "user":
                    content = str(msg.get("content", ""))
                    current_title = content[:20] + ("..." if len(content) > 20 else "")
                    break
        data = {"title": current_title, "messages": messages}
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def send_message(self, chat_id: str, user_message: str, model_limit: int = 1500) -> dict:
        messages = self.load_chat(chat_id)
        
        request_tokens = self.count_tokens(user_message)
        history_tokens = self.count_messages_tokens(messages)
        total_input_tokens = history_tokens + request_tokens
        
        # Фиксируем попытку для отображения в сайдбаре даже при ошибке
        self.last_attempt = {
            "history_tokens": history_tokens,
            "request_tokens": request_tokens,
            "total_input_tokens": total_input_tokens
        }
        
        if total_input_tokens > model_limit:
            raise ValueError(
                f"🚨 ПЕРЕПОЛНЕНИЕ ЛИМИТА КОНТЕКСТА!\n\n"
                f"• История чата: {history_tokens} токенов\n"
                f"• Запрос: {request_tokens} токенов\n"
                f"• Суммарно на входе: {total_input_tokens} / {model_limit} токенов\n\n"
                f"❌ Ошибка: контекст исчерпан, модель больше не принимает запрос."
            )

        messages.append({"role": "user", "content": user_message})

        api_key = os.environ.get("LITELLM_API_KEY") or "sk-L2Fx4Xsvy_OA6gcp3gG2pA"
        client = OpenAI(
            api_key=api_key,
            base_url="https://llm.effective.land/v1",
        )

        response = client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.7,
            timeout=30
        )
        answer = response.choices[0].message.content
        response_tokens = response.usage.completion_tokens if hasattr(response, "usage") else self.count_tokens(answer)

        messages.append({"role": "assistant", "content": answer})
        
        chats = self.get_all_chats()
        title = chats.get(chat_id, {}).get("title", "Новый диалог")
        self.save_chat(chat_id, title, messages)

        return {
            "answer": answer,
            "request_tokens": request_tokens,
            "history_tokens": history_tokens,
            "response_tokens": response_tokens,
            "total_turn_tokens": request_tokens + response_tokens,
            "cumulative_tokens": history_tokens + request_tokens + response_tokens
        }

    def delete_chat(self, chat_id: str):
        filepath = os.path.join(self.storage_dir, f"{chat_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
