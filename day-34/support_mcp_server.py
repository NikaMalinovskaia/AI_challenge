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

def support_create_ticket(user_id: str, user_name: str, issue: str):
    db = load_db()
    db["counter"] += 1
    new_id = f"T-{db['counter']}"
    db["tickets"][new_id] = {
        "ticket_id": new_id,
        "user_id": user_id,
        "user_name": user_name,
        "issue": issue,
        "status": "open",
        "created_at": "2026-10-18"
    }
    save_db(db)
    return {"status": "success", "ticket_id": new_id, "message": f"Тикет {new_id} создан."}

def list_directory(path: str = ".") -> list:
    ignored = {".git", "__pycache__", ".pytest_cache", "venv", "env", "node_modules", "data"}
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
        return {"error": f"Файл не найден: {file_path}"}
    try:
        with open(safe_path, "r", encoding="utf-8") as f:
            return {"file_path": file_path, "content": f.read()}
    except Exception as e:
        return {"error": str(e)}

def write_file_content(file_path: str, content: str) -> dict:
    """Создает новый файл или перезаписывает существующий (для генерации README/ADR/документации)."""
    safe_path = os.path.normpath(file_path)
    try:
        os.makedirs(os.path.dirname(safe_path) if os.path.dirname(safe_path) else ".", exist_ok=True)
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)
        return {"status": "success", "file_path": file_path, "message": f"Файл успешно записан/обновлен."}
    except Exception as e:
        return {"error": f"Ошибка записи файла: {e}"}

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
                                "name": "support_create_ticket",
                                "description": "Создать тикет в CRM.",
                                "inputSchema": {"type": "object", "properties": {"user_id": {"type": "string"}, "user_name": {"type": "string"}, "issue": {"type": "string"}}, "required": ["user_id", "user_name", "issue"]}
                            },
                            {
                                "name": "list_directory",
                                "description": "Посмотреть содержимое папки репозитория.",
                                "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}}}
                            },
                            {
                                "name": "read_file_content",
                                "description": "Прочитать текст файла.",
                                "inputSchema": {"type": "object", "properties": {"file_path": {"type": "string"}}, "required": ["file_path"]}
                            },
                            {
                                "name": "write_file_content",
                                "description": "Создать или обновить файл (например, документацию, README, ADR).",
                                "inputSchema": {"type": "object", "properties": {"file_path": {"type": "string"}, "content": {"type": "string"}}, "required": ["file_path", "content"]}
                            }
                        ]
                    }
                }
            elif method == "tools/call":
                name = params.get("name")
                args = params.get("arguments", {})
                
                if name == "support_create_ticket":
                    res = support_create_ticket(args.get("user_id"), args.get("user_name"), args.get("issue"))
                elif name == "list_directory":
                    res = list_directory(args.get("path", "."))
                elif name == "read_file_content":
                    res = read_file_content(args.get("file_path"))
                elif name == "write_file_content":
                    res = write_file_content(args.get("file_path"), args.get("content"))
                else:
                    res = {"error": f"Tool not found: {name}"}

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
