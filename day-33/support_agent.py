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

def load_faq_kb():
    faq_dir = "support/faq"
    docs = []
    if os.path.exists(faq_dir):
        for fname in os.listdir(faq_dir):
            if fname.endswith(".md"):
                with open(os.path.join(faq_dir, fname), "r", encoding="utf-8") as f:
                    docs.append(f.read())
    return "\n\n".join(docs) if docs else "FAQ пуст."

def run_interactive_support():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Ошибка: не задан OPENAI_API_KEY")
        return

    print("--- 🤖 Инициализация технической поддержки с MCP-доступом к коду ---")
    user_id = input("Введите ваш ID (например, u-105): ").strip()
    user_name = input("Введите ваше имя: ").strip()
    existing_ticket = input("Введите номер тикета, если он уже есть (или оставьте пустым): ").strip()
    
    print("\nАссистент готов. Задавайте вопросы по коду или проекту (для выхода введите 'exit'):")

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

    kb = load_faq_kb()
    client = OpenAI(api_key=api_key, base_url=os.getenv("LLM_BASE_URL", "https://llm.effective.land/v1"))

    while True:
        query = input("\nВы: ").strip()
        if query.lower() in ["exit", "quit", "выход"]:
            print("До свидания! Обращайтесь снова.")
            break
        if not query:
            continue

        system_prompt = f"""Ты — старший инженер технической поддержки и AI-ревьюер кода.
СТРОГИЕ ПРАВИЛА:
1. Если у пользователя нет открытого тикета, ты ОБЯЗАН в самом начале вызвать инструмент `support_create_ticket` для регистрации обращения.
2. Если пользователь просит проанализировать код, посмотреть папки или файлы, ты НЕ ИМЕЕШЬ ПРАВА отвечать текстом «я посмотрю». Ты ДОЛЖЕН реально вызвать инструменты `list_directory` или `read_file_content`.
3. Анализируй реальные данные, полученные от инструментов, и давай конкретные технические ответы.

База знаний FAQ:
{kb}
"""

        user_context_msg = f"Пользователь [{user_id}] ({user_name}) пишет: «{query}»."
        if existing_ticket:
            user_context_msg += f" У него уже есть открытый тикет: {existing_ticket}."
        else:
            user_context_msg += " Это первое обращение, номера тикета пока нет (обязательно создай его через инструмент)."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_context_msg}
        ]

        print("🤖 Ассистент связывается с CRM и сканирует репозиторий...")
        
        # Цикл многошагового вызова инструментов (Multi-step tool execution)
        for _ in range(5):  # Ограничение на количество шагов рекурсии вызовов
            response = client.chat.completions.create(
                model=os.getenv("LLM_MODEL", "glm-5.3-flash"),
                messages=messages,
                tools=openai_tools,
                tool_choice="auto",
                temperature=0.2
            )

            msg = response.choices[0].message
            
            # Если модель больше не вызывает инструменты — выводим ответ пользователю
            if not msg.tool_calls:
                print(f"\n💬 Поддержка: {msg.content}")
                break

            messages.append(msg)
            for call in msg.tool_calls:
                t_name = call.function.name
                t_args = json.loads(call.function.arguments)
                print(f"🔌 [MCP Action] Вызов инструмента '{t_name}' с аргументами {t_args}")
                
                tool_res = mcp.call_tool(t_name, t_args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": tool_res
                })

    mcp.close()

if __name__ == "__main__":
    run_interactive_support()
