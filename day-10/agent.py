import os
import json
import time
from openai import OpenAI
import tiktoken

class MultiStrategyAgent:
    def __init__(self, model_name: str = "glm-4.7-flash", storage_dir: str = "chats_storage_day10"):
        self.model_name = model_name
        self.storage_dir = storage_dir
        
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

    def create_new_chat(self, strategy: str = "sliding_window") -> str:
        chat_id = str(int(time.time()))
        initial_msg = {"role": "system", "content": "Ты — профессиональный системный аналитик, помогающий составить подробное ТЗ."}
        
        data = {
            "title": "Новое ТЗ",
            "strategy": strategy, # "sliding_window", "sticky_facts", "branching"
            "messages": [initial_msg],
            "facts": {
                "цель": "не указана",
                "ограничения": "не указаны",
                "предпочтения": "не указаны",
                "решения": "нет",
                "договоренности": "нет"
            },
            "branches": {
                "main": [initial_msg]
            },
            "active_branch": "main"
        }
        self.save_chat_data(chat_id, data)
        return chat_id

    def load_chat_data(self, chat_id: str) -> dict:
        filepath = os.path.join(self.storage_dir, f"{chat_id}.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "strategy" not in data:
                        data["strategy"] = "sliding_window"
                    if "facts" not in data:
                        data["facts"] = {"цель": "не указана", "ограничения": "не указаны", "предпочтения": "не указаны"}
                    if "branches" not in data:
                        data["branches"] = {"main": list(data.get("messages", []))}
                    if "active_branch" not in data:
                        data["active_branch"] = "main"
                    return data
            except Exception:
                pass
        return {
            "title": "Новое ТЗ",
            "strategy": "sliding_window",
            "messages": [{"role": "system", "content": "Ты — аналитик."}],
            "facts": {"цель": "не указана"},
            "branches": {"main": [{"role": "system", "content": "Ты — аналитик."}]},
            "active_branch": "main"
        }

    def save_chat_data(self, chat_id: str, data: dict):
        filepath = os.path.join(self.storage_dir, f"{chat_id}.json")
        msgs = data.get("messages", [])
        if data.get("title", "Новое ТЗ") == "Новое ТЗ":
            for m in msgs:
                if m["role"] == "user":
                    content = str(m.get("content", ""))
                    data["title"] = content[:22] + ("..." if len(content) > 22 else "")
                    break
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

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
                            "title": data.get("title", "Диалог"),
                            "strategy": data.get("strategy", "sliding_window")
                        }
                except Exception:
                    pass
        return chats

    def update_facts_from_dialog(self, chat_data: dict, new_user_msg: str, assistant_resp: str):
        current_facts = chat_data.get("facts", {})
        prompt = (
            f"Текущие факты о проекте/ТЗ:\n{json.dumps(current_facts, ensure_ascii=False)}\n\n"
            f"Последнее сообщение пользователя: {new_user_msg}\n"
            f"Ответ ассистента: {assistant_resp}\n\n"
            "Обнови JSON с фактами (ключи: цель, ограничения, предпочтения, решения, договоренности), "
            "добавив новую информацию, если она появилась. Верни ТОЛЬКО валидный JSON без лишнего текста."
        )
        api_key = os.environ.get("LITELLM_API_KEY") or "sk-L2Fx4Xsvy_OA6gcp3gG2pA"
        client = OpenAI(api_key=api_key, base_url="https://llm.effective.land/v1")
        try:
            resp = client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                timeout=20
            )
            content = resp.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                chat_data["facts"] = parsed
        except Exception:
            pass

    def prepare_request_messages(self, chat_data: dict, keep_last_n: int = 6) -> list:
        strategy = chat_data.get("strategy", "sliding_window")
        
        if strategy == "branching":
            active_branch = chat_data.get("active_branch", "main")
            messages = chat_data["branches"].get(active_branch, chat_data.get("messages", []))
        else:
            messages = chat_data.get("messages", [])

        system_msg = messages[0] if messages and messages[0]["role"] == "system" else {"role": "system", "content": "Ты — аналитик."}
        history = messages[1:] if messages and messages[0]["role"] == "system" else messages

        if strategy == "sliding_window":
            trimmed_history = history[-keep_last_n:]
            return [system_msg] + trimmed_history
            
        elif strategy == "sticky_facts":
            facts = chat_data.get("facts", {})
            facts_block = {"role": "system", "content": f"[АКТУАЛЬНЫЕ ФАКТЫ О ПРОЕКТЕ / КВ-ПАМЯТЬ]:\n{json.dumps(facts, ensure_ascii=False, indent=2)}"}
            trimmed_history = history[-keep_last_n:]
            return [system_msg, facts_block] + trimmed_history
            
        elif strategy == "branching":
            return [system_msg] + history
            
        return messages

    def create_branch(self, chat_id: str, branch_name: str) -> bool:
        chat_data = self.load_chat_data(chat_id)
        if chat_data.get("strategy") != "branching":
            return False
        active_b = chat_data.get("active_branch", "main")
        current_msgs = list(chat_data["branches"].get(active_b, chat_data["messages"]))
        
        chat_data["branches"][branch_name] = current_msgs
        chat_data["active_branch"] = branch_name
        self.save_chat_data(chat_id, chat_data)
        return True

    def switch_branch(self, chat_id: str, branch_name: str):
        chat_data = self.load_chat_data(chat_id)
        if branch_name in chat_data.get("branches", {}):
            chat_data["active_branch"] = branch_name
            chat_data["messages"] = list(chat_data["branches"][branch_name])
            self.save_chat_data(chat_id, chat_data)

    def send_message(self, chat_id: str, user_message: str, keep_last_n: int = 6) -> dict:
        chat_data = self.load_chat_data(chat_id)
        strategy = chat_data.get("strategy", "sliding_window")
        
        if strategy == "branching":
            active_b = chat_data.get("active_branch", "main")
            if active_b not in chat_data["branches"]:
                chat_data["branches"][active_b] = list(chat_data["messages"])
            chat_data["branches"][active_b].append({"role": "user", "content": user_message})
            chat_data["messages"] = chat_data["branches"][active_b]
        else:
            chat_data["messages"].append({"role": "user", "content": user_message})
            
        request_msgs = self.prepare_request_messages(chat_data, keep_last_n=keep_last_n)
        
        request_tokens = self.count_tokens(user_message)
        history_tokens = self.count_messages_tokens(request_msgs)

        api_key = os.environ.get("LITELLM_API_KEY") or "sk-L2Fx4Xsvy_OA6gcp3gG2pA"
        client = OpenAI(api_key=api_key, base_url="https://llm.effective.land/v1")

        response = client.chat.completions.create(
            model=self.model_name,
            messages=request_msgs,
            temperature=0.7,
            timeout=30
        )
        answer = response.choices[0].message.content
        response_tokens = response.usage.completion_tokens if hasattr(response, "usage") else self.count_tokens(answer)

        if strategy == "branching":
            active_b = chat_data.get("active_branch", "main")
            chat_data["branches"][active_b].append({"role": "assistant", "content": answer})
            chat_data["messages"] = chat_data["branches"][active_b]
        else:
            chat_data["messages"].append({"role": "assistant", "content": answer})

        if strategy == "sticky_facts":
            self.update_facts_from_dialog(chat_data, user_message, answer)

        self.save_chat_data(chat_id, chat_data)

        return {
            "answer": answer,
            "request_tokens": request_tokens,
            "history_tokens": history_tokens,
            "response_tokens": response_tokens,
            "cumulative_tokens": history_tokens + request_tokens + response_tokens
        }

    def delete_chat(self, chat_id: str):
        filepath = os.path.join(self.storage_dir, f"{chat_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
