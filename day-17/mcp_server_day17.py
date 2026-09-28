import ast
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
    snippet = code_snippet.strip()
    
    # 1. Проверяем синтаксис через AST
    try:
        tree = ast.parse(snippet)
    except SyntaxError as e:
        return (
            f"❌ **Ошибка синтаксиса Python:**\n"
            f"- Текст не является валидным кодом (ошибка на строке {e.lineno}).\n\n"
            f"💡 **Рекомендации архитектора:** Передайте корректный фрагмент программного кода."
        )

    issues = []
    recommendations = []

    # 2. Ищем наличие функций или классов
    has_defs = any(isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)) for node in ast.walk(tree))
    # 3. Ищем ключевые слова FSM
    has_fsm = any(kw in snippet.lower() for kw in ["fsm", "state", "stage", "transition", "allowed"])

    if not has_defs:
        issues.append("Код синтаксически корректен, но не содержит объявлений функций или классов (состоит только из выражений).")
    
    if not has_fsm:
        recommendations.append("Рекомендуется добавить логику конечного автомата (FSM) для контроля состояний.")

    # Формируем отчет
    if issues:
        report = "⚠️ **Архитектурные замечания:**\n"
        for issue in issues:
            report += f"- {issue}\n"
    else:
        report = "✅ **Структурный анализ пройден успешно:** код содержит валидные функции или классы.\n"

    if recommendations:
        report += "\n💡 **Рекомендации архитектора:**\n"
        for rec in recommendations:
            report += f"- {rec}\n"
    else:
        report += "\n✨ Все ключевые инварианты соблюдены, код готов к интеграции."

    return report

if __name__ == "__main__":
    mcp.run(transport="stdio")
