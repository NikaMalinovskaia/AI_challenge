import os
import json
import time
from openai import OpenAI
import tiktoken

class CompressionAgent:
    def __init__(self, model_name: str = "glm-4.7-flash", storage_dir: str = "chats_storage_day9"):
        self.model_name = model_name
        self.storage_dir = storage_dir
        self.last_compression_stats = None
        
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
                            "messages": data.get("messages", []),
                            "summary": data.get("summary", "")
                        }
                except Exception:
                    pass
        return chats

    def create_new_chat(self) -> str:
        chat_id = str(int(time.time()))
        initial_msgs = [
            {"role": "system", "content": "Ты — полезный и лаконичный AI-ассистент."},
        ]
        data = {
            "title": "Новый диалог",
            "messages": initial_msgs,  # Здесь хранятся ТОЛЬКО последние сообщения "как есть"
            "summary": "",             # Summary хранится ОТДЕЛЬНО
            "full_history_backup": list(initial_msgs) # Для честного сравнения токенов без сжатия
        }
        self.save_chat_data(chat_id, data)
        self.last_compression_stats = None
        return chat_id

    def load_chat_data(self, chat_id: str) -> dict:
        filepath = os.path.join(self.storage_dir, f"{chat_id}.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "full_history_backup" not in data:
                        data["full_history_backup"] = list(data.get("messages", []))
                    return data
            except Exception:
                pass
        initial_msgs = [{"role": "system", "content": "Ты — полезный и лаконичный AI-ассистент."}]
        return {
            "title": "Новый диалог",
            "messages": initial_msgs,
            "summary": "",
            "full_history_backup": list(initial_msgs)
        }

    def save_chat_data(self, chat_id: str, data: dict):
        filepath = os.path.join(self.storage_dir, f"{chat_id}.json")
        if data.get("title", "Новый диалог") == "Новый диалог":
            for msg in data.get("messages", []):
                if msg["role"] == "user":
                    content = str(msg.get("content", ""))
                    data["title"] = content[:20] + ("..." if len(content) > 20 else "")
                    break
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_prepared_request_messages(self, chat_data: dict) -> list:
        """Динамически собирает запрос: [Системный] + [Отдельный Summary как контекст] + [Последние N сообщений «как есть»]"""
        messages = chat_data.get("messages", [])
        summary = chat_data.get("summary", "")
        
        system_prompt = messages[0] if messages and messages[0]["role"] == "system" else {"role": "system", "content": "Ты — помощник."}
        recent_messages = messages[1:] if messages and messages[0]["role"] == "system" else messages
        
        prepared = [system_prompt]
        if summary:
            # Подставляем summary отдельно вместо полной старой истории
            prepared.append({"role": "system", "content": f"[ОТДЕЛЬНЫЙ СЖАТЫЙ КОНТЕКСТ (SUMMARY)]: {summary}"})
        prepared.extend(recent_messages)
        return prepared

    def compress_history(self, chat_id: str, keep_last_n: int = 4):
        """Сжимает старую историю в отдельное summary, обрезая messages до последних N сообщений"""
        chat_data = self.load_chat_data(chat_id)
        backup_msgs = chat_data["full_history_backup"]
        
        system_prompt = backup_msgs[0] if backup_msgs and backup_msgs[0]["role"] == "system" else {"role": "system", "content": "Ты — помощник."}
        chat_messages = backup_msgs[1:] if backup_msgs and backup_msgs[0]["role"] == "system" else backup_msgs
        
        if len(chat_messages) <= keep_last_n:
            return False
            
        tokens_before = self.count_messages_tokens(backup_msgs)
        
        # Отделяем старые для суммаризации и последние N "как есть"
        old_messages = chat_messages[:-keep_last_n]
        recent_messages = chat_messages[-keep_last_n:]
        
        old_text = "\n".join([f"{m['role']}: {m['content']}" for m in old_messages])
        existing_summary = chat_data.get("summary", "")
        
        summary_prompt = (
            f"Ранее был такой контекст:\n{existing_summary}\n\n"
            f"Новые сообщения для добавления в резюме:\n{old_text}\n\n"
            "Сделай емкое summary. ВАЖНО: строго соблюдай хронологический порядок событий "
            "(что было в самом начале диалога, должно стоять на первом месте), "
            "сохранив ключевые факты и темы."
        )

        api_key = os.environ.get("LITELLM_API_KEY") or "sk-L2Fx4Xsvy_OA6gcp3gG2pA"
        client = OpenAI(api_key=api_key, base_url="https://llm.effective.land/v1")
        
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.3,
            timeout=30
        )
        new_summary = response.choices[0].message.content

        # В messages записываем ТОЛЬКО системный промпт и последние N сообщений "как есть"
        new_messages_storage = [system_prompt] + recent_messages
        
        # Считаем токены с подставленным отдельным summary
        temp_data_for_count = {"messages": new_messages_storage, "summary": new_summary}
        tokens_after = self.count_messages_tokens(self.get_prepared_request_messages(temp_data_for_count))
        
        chat_data["summary"] = new_summary
        chat_data["messages"] = new_messages_storage
        self.save_chat_data(chat_id, chat_data)
        
        self.last_compression_stats = {
            "tokens_before": tokens_before,
            "tokens_after": tokens_after,
            "saved_tokens": tokens_before - tokens_after,
            "summary": new_summary
        }
        return True

    def compare_responses(self, chat_id: str, test_prompt: str) -> dict:
        chat_data = self.load_chat_data(chat_id)
        raw_msgs = list(chat_data["full_history_backup"])
        raw_msgs.append({"role": "user", "content": test_prompt})
        
        compressed_msgs = list(self.get_prepared_request_messages(chat_data))
        compressed_msgs.append({"role": "user", "content": test_prompt})
        
        tokens_without = self.count_messages_tokens(raw_msgs)
        tokens_with = self.count_messages_tokens(compressed_msgs)
        
        api_key = os.environ.get("LITELLM_API_KEY") or "sk-L2Fx4Xsvy_OA6gcp3gG2pA"
        client = OpenAI(api_key=api_key, base_url="https://llm.effective.land/v1")
        
        resp_wo = client.chat.completions.create(model=self.model_name, messages=raw_msgs, temperature=0.7)
        answer_without = resp_wo.choices[0].message.content
        
        resp_w = client.chat.completions.create(model=self.model_name, messages=compressed_msgs, temperature=0.7)
        answer_with = resp_w.choices[0].message.content
        
        return {
            "tokens_without": tokens_without,
            "tokens_with": tokens_with,
            "saved": tokens_without - tokens_with,
            "answer_without": answer_without,
            "answer_with": answer_with
        }

    def send_message(self, chat_id: str, user_message: str, auto_compress_threshold: int = 8, keep_last_n: int = 4) -> dict:
        chat_data = self.load_chat_data(chat_id)
        
        # Пишем в полный бэкап
        chat_data["full_history_backup"].append({"role": "user", "content": user_message})
        
        # Пишем в активное хранение последних сообщений
        chat_data["messages"].append({"role": "user", "content": user_message})
        
        # Проверяем порог автосжатия по количеству реплик в бэкапе
        chat_msg_count = len([m for m in chat_data["full_history_backup"] if m["role"] != "system"])
        
        if chat_msg_count >= auto_compress_threshold:
            self.save_chat_data(chat_id, chat_data)
            self.compress_history(chat_id, keep_last_n=keep_last_n)
            chat_data = self.load_chat_data(chat_id)
        else:
            self.save_chat_data(chat_id, chat_data)

        # Собираем итоговый массив сообщений для отправки (Summary отдельно + Последние N)
        request_messages = self.get_prepared_request_messages(chat_data)
        request_tokens = self.count_tokens(user_message)
        history_tokens = self.count_messages_tokens(request_messages)

        api_key = os.environ.get("LITELLM_API_KEY") or "sk-L2Fx4Xsvy_OA6gcp3gG2pA"
        client = OpenAI(api_key=api_key, base_url="https://llm.effective.land/v1")

        response = client.chat.completions.create(
            model=self.model_name,
            messages=request_messages,
            temperature=0.7,
            timeout=30
        )
        answer = response.choices[0].message.content
        response_tokens = response.usage.completion_tokens if hasattr(response, "usage") else self.count_tokens(answer)

        # Добавляем ответ в бэкап и в последние сообщения "как есть"
        chat_data["full_history_backup"].append({"role": "assistant", "content": answer})
        chat_data["messages"].append({"role": "assistant", "content": answer})
        
        # Следим, чтобы в active messages оставалось не больше keep_last_n пар (или реплик) плюс системный
        system_prompt = chat_data["messages"][0] if chat_data["messages"] and chat_data["messages"][0]["role"] == "system" else None
        non_system = [m for m in chat_data["messages"] if m["role"] != "system"]
        if len(non_system) > (keep_last_n * 2): # с запасом на пары вопрос-ответ
            non_system = non_system[-(keep_last_n * 2):]
        
        chat_data["messages"] = ([system_prompt] if system_prompt else []) + non_system
        self.save_chat_data(chat_id, chat_data)

        return {
            "answer": answer,
            "request_tokens": request_tokens,
            "history_tokens": history_tokens,
            "response_tokens": response_tokens,
            "cumulative_tokens": history_tokens + request_tokens + response_tokens,
            "compression_stats": self.last_compression_stats
        }

    def delete_chat(self, chat_id: str):
        filepath = os.path.join(self.storage_dir, f"{chat_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
