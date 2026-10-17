import requests
import time
from mcp_git import get_git_branch_info, get_github_repo_tree, read_github_file

class DevAssistantAgent:
    def __init__(self, model_name: str = "qwen2.5", temperature: float = 0.1, max_tokens: int = 1000):
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.local_model = model_name
        self.ollama_url = "http://localhost:11434/api/generate"
        self.reset_memory()

    def chat(self, user_message: str) -> tuple:
        start_time = time.time()
        
        msg_trimmed = user_message.strip()
        if msg_trimmed.startswith("/help"):
            git_info = get_git_branch_info()
            tree_info = get_github_repo_tree("")
            answer = (
                f"## 📌 Справка по проекту\n\n"
                f"**Репозиторий:** `NikaMalinovskaia/AI_challenge`\n"
                f"- **Git:** {git_info}\n\n"
                f"**Структура репозитория (корень):**\n```text\n{tree_info}\n```\n\n"
                f"Вы можете попросить меня открыть любую папку (например, *'покажи содержимое day-2'*) или прочитать конкретный файл."
            )
            duration = time.time() - start_time
            self.history.append({"role": "user", "content": user_message})
            self.history.append({"role": "assistant", "content": answer})
            return answer, duration

        user_lower = user_message.lower()
        tool_output = ""
        
        if "day-" in user_lower or "папк" in user_lower or "содержим" in user_lower:
            words = user_message.split()
            target_path = ""
            for word in words:
                if "day-" in word.lower():
                    target_path = word.strip(".,!?")
                    break
            
            if target_path:
                tool_output = f"\n[Содержимое папки '{target_path}' с GitHub]:\n{get_github_repo_tree(target_path)}"
            else:
                tool_output = f"\n[Содержимое корня репозитория]:\n{get_github_repo_tree('')}"

        system_prompt = (
            "Ты — профессиональный AI-ассистент разработчика, работающий с репозиторием NikaMalinovskaia/AI_challenge. "
            "Используй предоставленные данные о структуре и файлах репозитория для подробных и точных ответов. "
            "Отвечай строго на русском языке.\n\n"
        )
        
        git_info = get_git_branch_info()
        context_block = f"## КОНТЕКСТ GIT\n- {git_info}\n\n"
        
        if tool_output:
            context_block += f"## ДАННЫЕ ИЗ РЕПОЗИТОРИЯ\n{tool_output}\n\n"

        history_text = ""
        for msg in self.history:
            role = "Пользователь" if msg["role"] == "user" else "Ассистент"
            history_text += f"{role}: {msg['content']}\n"

        full_prompt = system_prompt + context_block + history_text + f"Пользователь: {user_message}\nАссистент:"

        self.history.append({"role": "user", "content": user_message})
        
        try:
            payload = {
                "model": self.local_model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature, 
                    "num_predict": self.max_tokens,
                    "num_ctx": 4096
                }
            }
            
            res = requests.post(self.ollama_url, json=payload, timeout=90)
            if res.status_code != 200:
                raise Exception(f"Ошибка Ollama API: {res.status_code} - {res.text}")
                
            response_data = res.json()
            final_answer = response_data.get("response", "").strip()
            
            if not final_answer:
                final_answer = "Не удалось сформировать ответ. Попробуйте переформулировать запрос."

            duration = time.time() - start_time
            self.history.append({"role": "assistant", "content": final_answer})
            return final_answer, duration
            
        except Exception as e:
            self.history.pop()
            raise Exception(f"Ошибка в агенте: {e}")

    def reset_memory(self):
        self.history = []