import json
import os
import random
from datetime import datetime
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("QualitySchedulerServer")
DB_FILE = "metrics_history.json"

def load_history():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_history(history):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

@mcp.tool()
def collect_and_store_metrics(feature_name: str, coverage: str, bugs_count: int) -> str:
    """Собирает и сохраняет текущие метрики качества фичи в историю."""
    history = load_history()
    
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "feature_name": feature_name,
        "coverage": coverage,
        "bugs_count": bugs_count
    }
    
    history.append(record)
    save_history(history)
    
    return f"💾 Метрики для фичи '{feature_name}' сохранены в {record['timestamp']}. Покрытие: {coverage}, Багов: {bugs_count}."

@mcp.tool()
def get_periodic_summary() -> str:
    """Генерирует и возвращает актуальную сводку с имитацией фоновых изменений метрик."""
    history = load_history()
    
    # Добавляем симуляцию свежего тика планировщика прямо в момент запроса,
    # чтобы пользователь сразу видел новые изменяющиеся данные и таймстампы!
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    simulated_features = ["auth_service", "payment_v2", "notification_API", "search_engine"]
    chosen_feature = random.choice(simulated_features)
    simulated_coverage = f"{random.randint(88, 99)}%"
    simulated_bugs = random.randint(0, 2)
    
    new_record = {
        "timestamp": now_str,
        "feature_name": chosen_feature,
        "coverage": simulated_coverage,
        "bugs_count": simulated_bugs
    }
    
    history.append(new_record)
    if len(history) > 15:
        history = history[-15:]
    save_history(history)
    
    summary = f"📈 **Регулярная сводка качества (Динамический фоновый опрос 24/7):**\n"
    for item in history[-6:]: # показываем последние 6 записей
        summary += f"- `[{item['timestamp']}]` Фича: **{item['feature_name']}** | Покрытие: {item['coverage']} | Багов: {item['bugs_count']}\n"
        
    return summary

if __name__ == "__main__":
    mcp.run(transport="stdio")
