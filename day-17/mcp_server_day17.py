from mcp.server.mcpserver import MCPServer

# Создаем сервер с помощью нового класса MCPServer
mcp = MCPServer("QualityAgentServer")

@mcp.tool()
def check_test_status(feature_name: str) -> str:
    """Проверяет статус тест-кейсов и готовность фичи к релизу в контуре QA."""
    features_database = {
        "auth": {"status": "Passed", "coverage": "94%", "bugs": 0},
        "payment": {"status": "Failed", "coverage": "65%", "bugs": 2},
        "fsm_agent": {"status": "In Progress", "coverage": "88%", "bugs": 0}
    }
    
    feature_key = feature_name.lower()
    if feature_key in features_database:
        data = features_database[feature_key]
        return f"📊 Отчет по фиче '{feature_name}': Статус — {data['status']}, Покрытие — {data['coverage']}, Активных багов — {data['bugs']}."
    else:
        return f"⚠️ Фича '{feature_name}' не найдена в системе учета тестирования."

@mcp.tool()
def validate_code_invariants(code_snippet: str) -> str:
    """Проверяет код на соответствие инвариантам безопасности и FSM-архитектуры."""
    if "async" in code_snippet and "ClientSession" in code_snippet:
        return "✅ Инварианты соблюдены: обнаружено корректное асинхронное MCP-соединение."
    else:
        return "❌ Предупреждение: в коде не найдено защитных механизмов MCP/FSM."

if __name__ == "__main__":
    mcp.run(transport="stdio")
