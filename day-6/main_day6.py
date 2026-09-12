import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from agent import LLMAgent

def main():
    print("Инициализация агента (День 6)...")
    
    try:
        agent = LLMAgent(model_name="glm-4.7-flash")
        
        query_1 = "Запомни кодовое слово: 'Эльбрус'."
        print(f"\nПользователь: {query_1}")
        ans_1 = agent.chat(query_1)
        print(f"Агент: {ans_1}")
        
        query_2 = "Какое кодовое слово я попросил тебя запомнить?"
        print(f"\nПользователь: {query_2}")
        ans_2 = agent.chat(query_2)
        print(f"Агент: {ans_2}")
        
        report = f"# Отчет: День 6 (Первый агент)\n\n"
        report += f"**Запрос 1:** {query_1}\n**Ответ 1:** {ans_1}\n\n"
        report += f"**Запрос 2 (проверка контекста):** {query_2}\n**Ответ 2:** {ans_2}\n"
        
        with open("agent_output.md", "w", encoding="utf-8") as f:
            f.write(report)
            
        print("\n[УСПЕХ] Результат успешно сохранен в agent_output.md")
        # Больше здесь ничего не печатаем, отдаем управление bash-скрипту

    except Exception as e:
        print(f"\n[ОШИБКА] Что-то пошло не так во время работы агента: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
