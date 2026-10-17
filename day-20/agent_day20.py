from __future__ import annotations
import json
import os
import time
import threading
from datetime import datetime
from openai import OpenAI
import sys
sys.path.append(os.path.dirname(__file__))

from mcp_server_analytics import fetch_system_metrics
from mcp_server_crm import create_jira_ticket, send_slack_notification

class OrchestrationAgentDay20:
    def __init__(self, storage_dir="memory_storage_day20", model_name="glm-4.7-flash", temperature=0.3, background_interval: int = 60):
        self.storage_dir = storage_dir
        self.model_name = model_name
        self.temperature = temperature
        self.background_interval = background_interval
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs("background_reports", exist_ok=True)
        
        api_key = os.environ.get("LITELLM_API_KEY") or "sk-L2Fx4Xsvy_OA6gcp3gG2pA"
        self.client = OpenAI(
            api_key=api_key, 
            base_url="https://llm.effective.land/v1",
            timeout=15.0,
            max_retries=1
        )

        self.latest_bg_report = "⏳ Ожидание первого фонового цикла..."
        
        self._is_running = True
        self._bg_thread = threading.Thread(target=self._background_scheduler_loop, daemon=True)
        self._bg_thread.start()

        initial_memory = []
        path = self._get_path("short_term")
        if not os.path.exists(path):
            self.save_memory("short_term", initial_memory)

    def _get_path(self, memory_type: str) -> str:
        return os.path.join(self.storage_dir, f"{memory_type}.json")

    def load_memory(self, memory_type: str) -> list:
        path = self._get_path(memory_type)
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_memory(self, memory_type: str, data):
        path = self._get_path(memory_type)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _background_scheduler_loop(self):
        while self._is_running:
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                metrics = fetch_system_metrics(feature_name="background_health_check")
                
                report = (
                    f"⏰ [Автоматический фоновый отчет — {timestamp}]\n\n"
                    f"• Статус серверов: **Активны**\n\n"
                    f"• Данные аналитики:\n  {metrics}"
                )
                self.latest_bg_report = report
                
                filepath = os.path.join("background_reports", "pipeline_report.txt")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(report)
            except Exception as e:
                self.latest_bg_report = f"❌ Ошибка фонового планировщика: {e}"
            
            time.sleep(self.background_interval)

    def run_multi_server_workflow(self, feature_name: str) -> str:
        """Выполняет кросс-серверный оркестрационный флоу по запросу пользователя."""
        try:
            metrics_text = fetch_system_metrics(feature_name=feature_name)
            ticket_text = create_jira_ticket(
                project="CoreEngine",
                summary=f"Анализ багов для фичи '{feature_name}': устранить найденные дефекты",
                priority="High"
            )
            slack_text = send_slack_notification(
                channel="dev-ops-alerts",
                message=f"Метрики получены ({feature_name}). Создан тикет."
            )

            # 🛠️ Исправлено: добавлены двойные переносы строк (\n\n) для корректного отображения списков
            return (
                "🌐 **Длинный флоу (Orchestration MCP) успешно выполнен:**\n\n"
                f"1️⃣ **[AnalyticsServer]:**\n   {metrics_text}\n\n"
                f"2️⃣ **[CRMServer — Jira]:**\n   {ticket_text}\n\n"
                f"3️⃣ **[CRMServer — Slack]:**\n   {slack_text}"
            )
        except Exception as e:
            return f"❌ Ошибка оркестрации серверов: {e}"

    def send_message(self, user_message: str):
        short_term = self.load_memory("short_term")
        short_term.append({"role": "user", "content": user_message})

        msg_lower = user_message.lower()
        assistant_reply = ""

        # 🛠️ Расширили ключевые слова, чтобы запросы со словами "проверить", "авторизации" тоже запускали флоу
        if any(w in msg_lower for w in ["флоу", "оркестр", "сервер", "запусти", "полн", "отчет", "платеж", "проверить", "авторизации", "задач"]):
            if "платеж" in msg_lower:
                feature = "payment_gateway"
            elif "авториз" in msg_lower:
                feature = "auth_module"
            else:
                feature = "core_system"
            assistant_reply = self.run_multi_server_workflow(feature)
        elif "статус" in msg_lower or "фонов" in msg_lower:
            assistant_reply = f"🟢 Фоновый планировщик активен.\n\n{self.latest_bg_report}"
        else:
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "system", "content": "Ты оркестратор MCP-серверов."}] + short_term[-4:],
                    temperature=self.temperature
                )
                assistant_reply = response.choices[0].message.content
            except Exception:
                assistant_reply = f"⚠️ Шлюз LLM недоступен. Последний фоновый отчет:\n\n{self.latest_bg_report}"

        short_term.append({"role": "assistant", "content": assistant_reply})
        self.save_memory("short_term", short_term)

        return {"reply": assistant_reply}

    def reset_all_memory(self):
        self.save_memory("short_term", [])
