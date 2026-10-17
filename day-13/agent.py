from __future__ import annotations
import json
import os
from openai import OpenAI

class FSMTaskAgent:
    def __init__(self, storage_dir="memory_storage_day13", model_name="glm-4.7-flash", temperature=0.3):
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
                "stage": "planning",  # planning -> execution -> validation -> done
                "current_step": "Сбор требований и выбор стека",
                "expected_action": "Подтвердить стек технологий от пользователя"
            },
            "long_term": {
                "profile": "Senior Developer",
                "style": "Строгий, профессиональный, без «воды»."
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

    def update_fsm(self, stage: str, current_step: str, expected_action: str):
        """Обновление состояния конечного автомата задачи."""
        working = self.load_memory("working")
        working["stage"] = stage
        working["current_step"] = current_step
        working["expected_action"] = expected_action
        self.save_memory("working", working)

    def explicit_save(self, memory_type: str, key: str, value):
        mem = self.load_memory(memory_type)
        if isinstance(mem, dict):
            mem[key] = value
            self.save_memory(memory_type, mem)

    def count_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)

    def send_message(self, user_message: str, keep_last_n: int = 6):
        short_term = self.load_memory("short_term")
        working = self.load_memory("working")
        long_term = self.load_memory("long_term")

        short_term.append({"role": "user", "content": user_message})

        # АВТОМАТИЧЕСКОЕ ПЕРЕКЛЮЧЕНИЕ ЭТАПОВ ПО КЛЮЧЕВЫМ СЛОВАМ ПОЛЬЗОВАТЕЛЯ
        current_stage = working.get("stage", "planning")
        
        if current_stage == "planning" and any(w in user_message.lower() for w in ["подтвержд", "выбираем", "давай", "переход", "устраивает"]):
            self.update_fsm(
                stage="execution",
                current_step="Написание кода и реализация эндпоинтов",
                expected_action="Реализовать базовый функционал и сообщить о готовности"
            )
        elif current_stage == "execution" and any(w in user_message.lower() for w in ["провер", "тест", "готово", "валид"]):
            self.update_fsm(
                stage="validation",
                current_step="Тестирование и проверка критических путей",
                expected_action="Проверить код на ошибки"
            )

        # Перезагружаем working с обновленным статусом
        working = self.load_memory("working")

        # СИСТЕМНЫЙ ПРОМПТ С ТЕКУЩИМ СОСТОЯНИЕМ FSM
        system_prompt = (
            "Ты — ИИ-ассистент с управлением задачей через конечный автомат (FSM).\n\n"
            f"👤 ПРОФИЛЬ (LONG-TERM):\n{json.dumps(long_term, ensure_ascii=False, indent=2)}\n\n"
            f"⚙️ ТЕКУЩЕЕ СОСТОЯНИЕ ЗАДАЧИ (FSM WORKING):\n{json.dumps(working, ensure_ascii=False, indent=2)}\n\n"
            "Инструкция: Строго следуй текущему этапу задачи и помогай пользователю продвигаться дальше."
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
            "stage": "planning",
            "current_step": "Сбор требований и выбор стека",
            "expected_action": "Подтвердить стек технологий от пользователя"
        })
        self.save_memory("long_term", {
            "profile": "Senior Developer",
            "style": "Строгий, профессиональный, без «воды»."
        })
