import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from agent import LLMAgent

def main():
    print("--- ЗАПУСК 1: Начинаем диалог ---")
    
    # Удаляем файл истории перед тестом, чтобы начать с чистого листа
    if os.path.exists("chat_history.json"):
        os.remove("chat_history.json")
        
    agent_1 = LLMAgent()
    
    query_1 = "Привет! Запомни секретное слово: 'Альпинист'."
    print(f"Пользователь: {query_1}")
    ans_1 = agent_1.chat(query_1)
    print(f"Агент: {ans_1}\n")
    
    print("--- ПЕРЕЗАПУСК ПРИЛОЖЕНИЯ (создаем нового агента с тем же файлом истории) ---")
    del agent_1 # Имитируем полное уничтожение объекта/процесса
    
    agent_2 = LLMAgent() # Он должен подгрузить историю из chat_history.json
    
    query_2 = "Какое секретное слово я просил тебя запомнить?"
    print(f"Пользователь: {query_2}")
    ans_2 = agent_2.chat(query_2)
    print(f"Агент: {ans_2}")
    
    # Проверяем результат
    if "альпинист" in ans_2.lower():
        print("\n[УСПЕХ] Контекст успешно сохранился и восстановился после перезапуска!")
    else:
        print("\n[ВНИМАНИЕ] Агент не вспомнил слово. Проверьте сохранение файла.")

if __name__ == "__main__":
    main()
