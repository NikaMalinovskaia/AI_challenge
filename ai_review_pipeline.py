# ai_review_pipeline.py
import subprocess
import os

def get_git_diff():
    """Шаг 1: Получаем diff текущих изменений"""
    # Для теста возьмем diff последних изменений в репозитории
    diff = subprocess.check_output(["git", "diff"]).decode("utf-8")
    return diff

def get_rag_context():
    """Шаг 2: Имитация RAG (подтягиваем документацию / правила проекта)"""
    # В реальном проекте здесь поиск по векторной базе (Chroma/Milvus)
    project_docs = """
    Правила проекта:
    1. Запрещено использовать сырые SQL-запросы (f-strings в SQL), используйте ORM или параметризованные запросы.
    2. Вся работа с БД должна быть вынесена в слой repository, а не находиться в сервисах.
    3. Обязательно нужно обрабатывать закрытие соединений через try/finally или контекстный менеджер (with).
    """
    return project_docs

def generate_ai_review(diff, context):
    """Шаг 3: Генерация ревью (здесь вызов к LLM)"""
    prompt = f"""
    Ты — Senior Code Reviewer. Проанализируй изменения в коде (git diff) с учетом правил проекта (контекста).
    
    КОНТЕКСТ (Документация/Правила):
    {context}
    
    DIFF ИЗМЕНЕНИЙ:
    {diff}
    
    Выдай ответ строго по пунктам:
    - Потенциальные баги
    - Архитектурные проблемы
    - Рекомендации
    """
    
    # ТУТ ВМЕСТО ПРИНТА ИДЕТ ВЫЗОВ К LLM (например, OpenAI API или Ollama)
    print("--- ОТПРАВЛЯЕМ В LLM ПРИМЕРНО ЭТО ---")
    print(prompt)
    print("---------------------------------------")

if __name__ == "__main__":
    diff = get_git_diff()
    context = get_rag_context()
    
    if not diff.strip():
        print("⚠️ Нет изменений в git diff. Сделай изменения в файле перед запуском!")
    else:
        generate_ai_review(diff, context)