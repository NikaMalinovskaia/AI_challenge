from __future__ import annotations
import os
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("CRMServer")
TASKS_FILE = "crm_tasks.json"

@mcp.tool()
def create_jira_ticket(project: str, summary: str, priority: str) -> str:
    """Сервер CRM: Создает задачу (тикет) в Jira/трекере на основе переданных данных."""
    ticket_id = "PROJ-404"
    return f"🎫 [CRMServer] Успешно создан тикет #{ticket_id} в проекте '{project}' с приоритетом {priority}: '{summary}'."

@mcp.tool()
def send_slack_notification(channel: str, message: str) -> str:
    """Сервер CRM: Отправляет уведомление в корпоративный чат (Slack/Telegram)."""
    return f"📢 [CRMServer] Уведомление успешно отправлено в канал #{channel}: «{message}»"

if __name__ == "__main__":
    mcp.run(transport="stdio")
