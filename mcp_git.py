import requests
import base64
import subprocess

GITHUB_REPO_API = "https://api.github.com/repos/NikaMalinovskaia/AI_challenge"

def get_git_branch_info() -> str:
    """Возвращает текущую ветку и локальный статус Git."""
    try:
        branch = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, check=True).stdout.strip()
        status = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, check=True).stdout.strip()
        return f"Ветка: {branch} | Статус: {status if status else 'Чисто'}"
    except Exception:
        return "Локальный Git недоступен"

def get_github_repo_tree(path: str = "") -> str:
    """Получает список файлов и папок по заданному пути в репозитории NikaMalinovskaia/AI_challenge."""
    try:
        url = f"{GITHUB_REPO_API}/contents/{path}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            items = response.json()
            if isinstance(items, list):
                res = []
                for item in items:
                    t = "📁 Папка" if item["type"] == "dir" else "📄 Файл"
                    res.append(f"{t}: {item['path']}")
                return "\n".join(res)
            elif isinstance(items, dict):
                return f"📄 Файл: {items.get('path')}"
        return f"Путь '{path}' не найден."
    except Exception as e:
        return f"Ошибка запроса к GitHub API: {e}"

def read_github_file(file_path: str) -> str:
    """Скачивает и возвращает содержимое конкретного файла из репозитория по его полному пути."""
    try:
        url = f"{GITHUB_REPO_API}/contents/{file_path}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "content" in data:
                content_bytes = base64.b64decode(data["content"])
                return content_bytes.decode("utf-8", errors="ignore")
        return f"Не удалось прочитать файл: {file_path}"
    except Exception as e:
        return f"Ошибка при загрузке файла: {e}"