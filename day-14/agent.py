from __future__ import annotations
import json
import os
from openai import OpenAI

class InvariantTaskAgent:
    def __init__(self, storage_dir="memory_storage_day14", model_name="glm-4.7-flash", temperature=0.3):
        self.storage_dir = storage_dir
        self.model_name = model_name
        self.temperature = temperature
        os.makedirs(self.storage_dir, exist_ok=True)
        
        api_key = os.environ.get("LITELLM_API_KEY") or "sk-L2Fx4Xsvy_OA6gcp3gG2pA"
        
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://llm.effective.land/v1",
        )

        initial_structures = {
            "short_term": [],
            "working": {
                "stage": "execution",
                "current_step": "Реализация эндпоинтов",
                "expected_action": "Написать код строго по инвариантам"
            },
            "invariants": {
                "allowed_stack": ["FastAPI", "PostgreSQL", "SQLAlchemy", "AsyncIO"],
                "forbidden_technologies": ["MongoDB", "Django", "MySQL", "Sync drivers"],
                "business_rules": [
                    "Использовать только асинхронные вызовы к БД (AsyncSession).",
                    "Строго запрещено менять выбранную реляционную БД на NoSQL.",
                    "Все эндпоинты должны быть типизированы через Pydantic."
                ]
            }
        }
        
        for mem_type, default_val in initial_structures.items():
            path = self._get_path(mem_type)
            if not os.path.exists(path):
                self.save_memory(mem_type, default_val)

    def _get_path(self, memory_type: str) -> str:
        return os.path.join(self.storage_dir, f"{memory_type}.json")

    def load_memory(self, memory_type: str) -> dict | list:
        path = self._get_path(memory_type)
        if not os.path.exists(path):
            return [] if memory_type == "short_term" else {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_memory(self, memory_type: str, data):
        path = self._get_path(memory_type)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def update_invariants(self, new_invariants_dict: dict):
        """Полное обновление файла инвариантов."""
        self.save_memory("invariants", new_invariants_dict)

    def count_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)

    def send_message(self, user_message: str, keep_last_n: int = 6):
        short_term = self.load_memory("short_term")
        working = self.load_memory("working")
        invariants = self.load_memory("invariants")

        short_term.append({"role": "user", "content": user_message})

        # ЖЕСТКИЙ СИСТЕМНЫЙ ПРОМПТ С ИНВАРИАНТАМИ
        system_prompt = (
            "Ты — строгий Senior Lead Developer, контролирующий соблюдение архитектуры.\n\n"
            f"🛑 НЕОБХОДИМЫЕ ИНВАРИАНТЫ И ОГРАНИЧЕНИЯ (Нарушать строго запрещено!):\n{json.dumps(invariants, ensure_ascii=False, indent=2)}\n\n"
            f"⚙️ ТЕКУЩЕЕ СОСТОЯНИЕ ЗАДАЧИ (FSM):\n{json.dumps(working, ensure_ascii=False, indent=2)}\n\n"
            "⚠️ ПРАВИЛА ПОВЕДЕНИЯ:\n"
            "1. Анализируй запрос пользователя на предмет конфликта с инвариантами и бизнес-правилами.\n"
            "2. Если пользователь просит использовать запрещенную технологию (например, MongoDB, Django) или нарушить правила, ты ОБЯЗАН ОТКАЗАТЬ.\n"
            "3. Объясни причину отказа, сославшись на конкретный инвариант или бизнес-правило из системных данных."
        )

        messages_for_api = [{"role": "system", "content": system_prompt}]
        recent_messages = short_term[-keep_last_n:]
        messages_for_api.extend(recent_messages)

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages_for_api,
                temperature=self.temperature
            )
        except Exception as e:
            short_term.pop()
            self.save_memory("short_term", short_term)
            raise Exception(f"Ошибка API: {e}")

        assistant_reply = response.choices[0].message.content

        short_term.append({"role": "assistant", "content": assistant_reply})
        self.save_memory("short_term", short_term)

        full_context_str = system_prompt + "".join([m["content"] for m in recent_messages])
        req_tokens = self.count_tokens(user_message)
        hist_tokens = self.count_tokens(full_context_str)
        resp_tokens = self.count_tokens(assistant_reply)

        return {
            "reply": assistant_reply,
            "request_tokens": req_tokens,
            "history_tokens": hist_tokens,
            "response_tokens": resp_tokens,
            "cumulative_tokens": hist_tokens + resp_tokens
        }

    def reset_all_memory(self):
        self.save_memory("short_term", [])
        self.save_memory("working", {
            "stage": "execution",
            "current_step": "Реализация эндпоинтов",
            "expected_action": "Написать код строго по инвариантам"
        })
        self.save_memory("invariants", {
            "allowed_stack": ["FastAPI", "PostgreSQL", "SQLAlchemy", "AsyncIO"],
            "forbidden_technologies": ["MongoDB", "Django", "MySQL", "Sync drivers"],
            "business_rules": [
                "Использовать только асинхронные вызовы к БД (AsyncSession).",
                "Строго запрещено менять выбранную реляционную БД на NoSQL.",
                "Все эндпоинты должны быть типизированы через Pydantic."
            ]
        })
