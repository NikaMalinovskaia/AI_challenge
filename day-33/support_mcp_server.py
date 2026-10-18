import sys
import json
import os

DB_PATH = "data/tickets.json"

def load_db():
    if not os.path.exists(DB_PATH):
        return {"tickets": {}, "counter": 1000}
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    os.makedirs("data", exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def support_list_tickets():
    db = load_db()
    return list(db["tickets"].values())

def support_get_ticket(ticket_id: str):
    db = load_db()
    ticket = db["tickets"].get(ticket_id)
    if not ticket:
        return {"error": f"Тикет {ticket_id} не найден в системе."}
    return ticket

def support_create_ticket(user_id: str, user_name: str, issue: str):
    db = load_db()
    db["counter"] += 1
    new_id = f"T-{db['counter']}"
    
    new_ticket = {
        "ticket_id": new_id,
        "user_id": user_id,
        "user_name": user_name,
        "issue": issue,
        "status": "open",
        "created_at": "2026-10-18",
        "comments": []
    }
    db["tickets"][new_id] = new_ticket
    save_db(db)
    return {"status": "success", "ticket_id": new_id, "message": f"Обращение зарегистрировано под номером {new_id}"}

def list_directory(path: str = ".") -> list:
    ignored = {".git", "__pycache__", ".pytest_cache", "venv", "env", "node_modules"}
    items = []
    try:
        for entry in os.scandir(path):
            if entry.name in ignored:
                continue
            items.append({
                "name": entry.name,
                "type": "directory" if entry.is_dir() else "file",
                "path": entry.path
            })
        return items
    except Exception as e:
        return [{"error": str(e)}]

def read_file_content(file_path: str) -> dict:
    safe_path = os.path.normpath(file_path)
    if not os.path.exists(safe_path) or os.path.isdir(safe_path):
        return {"error": f"Файл не найден или это директория: {file_path}"}
    try:
        with open(safe_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"file_path": file_path, "content": content}
    except Exception as e:
        return {"error": f"Ошибка чтения файла: {e}"}

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            if method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": [
                            {
                                "name": "support_list_tickets",
                                "description": "Получить список всех тикетов поддержки.",
                                "inputSchema": {"type": "object", "properties": {}}
                            },
                            {
                                "name": "support_get_ticket",
                                "description": "Получить детали тикета по номеру.",
                                "inputSchema": {"type": "object", "properties": {"ticket_id": {"type": "string"}}, "required": ["ticket_id"]}
                            },
                            {
                                "name": "support_create_ticket",
                                "description": "Создать новое обращение (тикет) в CRM для пользователя.",
                                "inputSchema": {"type": "object", "properties": {"user_id": {"type": "string"}, "user_name": {"type": "string"}, "issue": {"type": "string"}}, "required": ["user_id", "user_name", "issue"]}
                            },
                            {
                                "name": "list_directory",
                                "description": "Посмотреть содержимое папки репозитория для выбора файла анализа кода.",
                                "inputSchema": {"type": "object", "properties": {"path": {"type": "string", "description": "Путь к папке (например 'day_2' или '.')"}}}
                            },
                            {
                                "name": "read_file_content",
                                "description": "Прочитать текст выбранного файла исходного кода или документации.",
                                "inputSchema": {"type": "object", "properties": {"file_path": {"type": "string", "description": "Путь к файлу"}}, "required": ["file_path"]}
                            }
                        ]
                    }
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                args = params.get("arguments", {})
                
                if tool_name == "support_list_tickets":
                    res = support_list_tickets()
                elif tool_name == "support_get_ticket":
                    res = support_get_ticket(args.get("ticket_id"))
                elif tool_name == "support_create_ticket":
                    res = support_create_ticket(args.get("user_id"), args.get("user_name"), args.get("issue"))
                elif tool_name == "list_directory":
                    res = list_directory(args.get("path", "."))
                elif tool_name == "read_file_content":
                    res = read_file_content(args.get("file_path"))
                else:
                    res = {"error": f"Инструмент {tool_name} не найден"}

                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(res, ensure_ascii=False)}]}
                }
            else:
                response = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}

            print(json.dumps(response, ensure_ascii=False), flush=True)
        except Exception as e:
            err_resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}}
            print(json.dumps(err_resp, ensure_ascii=False), flush=True)

if __name__ == "__main__":
    main()
