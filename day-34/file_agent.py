import os
import json
import subprocess
from openai import OpenAI

class MCPClient:
    def __init__(self, server_script="support_mcp_server.py"):
        self.process = subprocess.Popen(
            ["python3", server_script],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self.req_id = 0

    def _call(self, method, params=None):
        self.req_id += 1
        payload = {"jsonrpc": "2.0", "id": self.req_id, "method": method, "params": params or {}}
        self.process.stdin.write(json.dumps(payload) + "\n")
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        return json.loads(line) if line else {}

    def list_tools(self):
        resp = self._call("tools/list")
        return resp.get("result", {}).get("tools", [])

    def call_tool(self, name, arguments):
        resp = self._call("tools/call", {"name": name, "arguments": arguments})
        return resp.get("result", {}).get("content", [{}])[0].get("text", "{}")

    def close(self):
        self.process.terminate()

def run_file_agent():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Ошибка: не задан OPENAI_API_KEY")
        return

    print("--- 📁 Агент работы с файлами проекта (День 34) ---")
    goal = input("Введите вашу цель для агента (например: 'Проанализируй файлы проекта и создай файл ARCHITECTURE.md'): ").strip()
    if not goal:
        return

    mcp = MCPClient("support_mcp_server.py")
    tools = mcp.list_tools()
    openai_tools = [{
        "type": "function",
        "function": {
            "name": t["name"],
            "description": t["description"],
            "parameters": t["inputSchema"]
        }
    } for t in tools]

    system_prompt = """Ты — автономный AI-ассистент инженера по работе с файлами проекта.
Твоя задача — выполнять сложные инженерные цели (анализировать код в нескольких файлах, искать использование компонентов, генерировать или обновлять документацию, создавать файлы вроде README.md или ADR).
ПРАВИЛА:
1. Исследуй структуру проекта с помощью `list_directory` и `read_file_content`. Работай с несколькими файлами для полноты картины.
2. Самостоятельно принимай решения, какие файлы нужно прочитать.
3. Если цель подразумевает создание или обновление документации/файлов, используй инструмент `write_file_content`.
4. Действуй автономно, вызывая инструменты подряд, пока задача не будет полностью решена.
"""

    client = OpenAI(api_key=api_key, base_url=os.getenv("LLM_BASE_URL", "https://llm.effective.land/v1"))
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Цель проекта: {goal}"}
    ]

    print("\n🤖 Агент начал автономное выполнение задачи...")

    for _ in range(8):  #заходов вызовов инструментов
        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "glm-5.3-flash"),
            messages=messages,
            tools=openai_tools,
            tool_choice="auto",
            temperature=0.2
        )

        msg = response.choices[0].message
        if not msg.tool_calls:
            print(f"\n💬 Результат выполнения:\n{msg.content}")
            break

        messages.append(msg)
        for call in msg.tool_calls:
            t_name = call.function.name
            t_args = json.loads(call.function.arguments)
            print(f"🔌 [Инструмент] Вызов `{t_name}` с аргументами {t_args}")
            
            tool_res = mcp.call_tool(t_name, t_args)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": tool_res
            })

    mcp.close()

if __name__ == "__main__":
    run_file_agent()
