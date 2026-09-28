from __future__ import annotations
import json
import os
import asyncio
import re
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class GuardedFSMAgentWithMCPTools:
    def __init__(self, storage_dir="memory_storage_day17", model_name="glm-4.7-flash", temperature=0.3):
        self.storage_dir = storage_dir
        self.model_name = model_name
        self.temperature = temperature
        os.makedirs(self.storage_dir, exist_ok=True)

        self.ALLOWED_TRANSITIONS = {
            "planning": ["execution"],
            "execution": ["planning", "validation"],
            "validation": ["execution", "done"],
            "done": []
        }

        initial_structures = {
            "short_term": [],
            "working": {
                "stage": "planning",
                "current_step": "Настройка кастомного MCP-сервера",
                "expected_action": "Проверить вызов кастомных инструментов"
            },
            "invariants": {
                "allowed_stack": ["FastAPI", "PostgreSQL", "SQLAlchemy"],
                "strict_lifecycle": True
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

    def fetch_mcp_tools(self) -> list:
        """Получает список инструментов с кастомного MCP-сервера."""
        async def _run_mcp():
            server_params = StdioServerParameters(
                command="python3.11",
                args=["mcp_server_day17.py"],
            )
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    response = await session.list_tools()
                    return response.tools

        try:
            return asyncio.run(_run_mcp())
        except Exception as e:
            print(f"Error fetching tools: {e}")
            return []

    def call_mcp_tool(self, tool_name: str, arguments: dict) -> str:
        """Вызывает конкретный инструмент на MCP-сервере и возвращает его реальный результат."""
        async def _run_call():
            server_params = StdioServerParameters(
                command="python3.11",
                args=["mcp_server_day17.py"],
            )
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)
                    return result.content[0].text

        try:
            return asyncio.run(_run_call())
        except Exception as e:
            return f"❌ Ошибка подключения к MCP-серверу: {e}"

    def change_stage(self, new_stage: str) -> tuple[bool, str]:
        working = self.load_memory("working")
        current_stage = working.get("stage", "planning")
        if current_stage == new_stage:
            return True, f"Уже на этапе {current_stage}."
        
        allowed_next = self.ALLOWED_TRANSITIONS.get(current_stage, [])
        if new_stage not in allowed_next:
            return False, f"🛑 Переход из '{current_stage}' в '{new_stage}' заблокирован FSM."

        working["stage"] = new_stage
        self.save_memory("working", working)
        return True, f"Успешный переход в этап: {new_stage}."

    def send_message(self, user_message: str):
        short_term = self.load_memory("short_term")
        working = self.load_memory("working")
        
        short_term.append({"role": "user", "content": user_message})

        user_msg_lower = user_message.lower()
        if any(w in user_msg_lower for w in ["код", "fastapi", "проверь", "validate", "def", "fsm", "print", "class"]):
            tool_name = "validate_code_invariants"
            
            # Надежная очистка префиксов через регулярные выражения
            clean_code = re.sub(r'^(проверь\s*код[:]?|код[:]?|проверь[:]?)\s*', '', user_message, flags=re.IGNORECASE).strip()

            tool_args = {"code_snippet": clean_code}
        else:
            tool_name = "check_test_status"
            feature = "payment" if "payment" in user_msg_lower else "auth"
            tool_args = {"feature_name": feature}

        tool_result = self.call_mcp_tool(tool_name, tool_args)

        assistant_reply = (
            f"🤖 **AI Quality Architect (FSM Stage: {working.get('stage')})**\n\n"
            f"Запрос проанализирован. Инициирован вызов MCP-инструмента: `{tool_name}`.\n\n"
            f"📊 **Результат выполнения MCP-инструмента:**\n"
            f"> {tool_result}\n\n"
            f"*Архитектурный вердикт:* Проверка завершена в соответствии с регламентом контроля инвариантов."
        )

        short_term.append({"role": "assistant", "content": assistant_reply})
        self.save_memory("short_term", short_term)

        return {"reply": assistant_reply}

    def reset_all_memory(self):
        self.save_memory("short_term", [])
        self.save_memory("working", {"stage": "planning"})
