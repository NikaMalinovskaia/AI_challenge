from __future__ import annotations
import json
import os
import asyncio
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class GuardedFSMAgentWithMCPTools:
    def __init__(self, storage_dir="memory_storage_day17", model_name="glm-4.7-flash", temperature=0.3):
        self.storage_dir = storage_dir
        self.model_name = model_name
        self.temperature = temperature
        os.makedirs(self.storage_dir, exist_ok=True)
        
        api_key = os.environ.get("LITELLM_API_KEY") or "sk-L2Fx4Xsvy_OA6gcp3gG2pA"
        self.client = OpenAI(api_key=api_key, base_url="https://llm.effective.land/v1")

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

    def fetch_mcp_tools(self) -> list | str:
        """Получает список инструментов с НАШЕГО кастомного MCP-сервера или возвращает текст подробной ошибки."""
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
            err_msg = str(e)
            # Извлекаем подробности из TaskGroup, если они есть
            if hasattr(e, "exceptions"):
                err_msg = ", ".join([str(sub) for sub in e.exceptions])
            return f"⚠️ Ошибка запуска MCP-сервера: {err_msg}"

    def call_mcp_tool(self, tool_name: str, arguments: dict) -> str:
        """Вызывает конкретный инструмент на MCP-сервере и возвращает результат."""
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
            err_msg = str(e)
            if hasattr(e, "exceptions"):
                err_msg = ", ".join([str(sub) for sub in e.exceptions])
            return f"❌ Ошибка вызова инструмента {tool_name}: {err_msg}"

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

        tools_result = self.fetch_mcp_tools()
        tools_desc = ""
        if isinstance(tools_result, list):
            tools_desc = "\n".join([f"- {t.name}: {t.description}" for t in tools_result])
        else:
            tools_desc = "Инструменты недоступны"

        tool_execution_result = ""
        if "статус" in user_message.lower() or "фич" in user_message.lower():
            feature = "payment" if "payment" in user_message.lower() else "auth"
            tool_execution_result = f"\n\n[Системный вызов MCP инструмента `check_test_status` для '{feature}']:\n" + self.call_mcp_tool("check_test_status", {"feature_name": feature})

        system_prompt = (
            "Ты — AI Quality Architect. Контролируй процесс через FSM.\n"
            f"Текущий этап: {working.get('stage')}\n"
            f"Доступные MCP-инструменты:\n{tools_desc}"
            f"{tool_execution_result}"
        )

        messages_for_api = [{"role": "system", "content": system_prompt}] + short_term[-6:]

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

        return {"reply": assistant_reply}

    def reset_all_memory(self):
        self.save_memory("short_term", [])
        self.save_memory("working", {"stage": "planning"})
