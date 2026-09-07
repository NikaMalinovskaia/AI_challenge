from agent import SimpleLLMAgent

def main():
    print("Инициализация агента...")
    # Создаем экземпляр агента как отдельную сущность
    agent = SimpleLLMAgent(model_name="glm-4.7-flash")
    
    test_query = "Расскажи в трех предложениях, что такое автономные AI-агенты."
    print(f"\nПользовательский запрос: {test_query}\n" + "-"*40)
    
    # Агент принимает запрос и возвращает результат
    answer = agent.run(test_query)
    
    print(f"Ответ агента:\n{answer}\n" + "-"*40)
    
    # Сохраняем результат в файл отчета
    report_content = f"# Отчет работы агента (День 6)\n\n"
    report_content += f"**Запрос:** {test_query}\n\n"
    report_content += f"**Ответ:**\n{answer}\n"
    
    with open("agent_output.md", "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print("Результат успешно сохранен в agent_output.md")

if __name__ == "__main__":
    main()
