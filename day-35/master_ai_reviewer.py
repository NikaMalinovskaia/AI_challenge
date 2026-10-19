import os
import sys
import glob
from openai import OpenAI

# Инициализация локального клиента Ollama
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

def load_criteria():
    """Загрузка методички с критериями оценки из criteria.md (RAG)"""
    criteria_path = "criteria.md"
    if os.path.exists(criteria_path):
        print(f"📚 Загрузка базы знаний (методички): {criteria_path}...")
        try:
            with open(criteria_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"⚠️ Не удалось прочитать {criteria_path}: {e}")
    return "Проверь инкапсуляцию, именование по стандартам C# и логику работы."

def scan_target_directory(target_path):
    """Сканирование всей папки/репозитория: сбор всех .cs файлов рекурсивно"""
    if not os.path.exists(target_path):
        print(f"❌ Ошибка: Путь не существует -> {target_path}")
        return []
    
    print(f"🔍 Рекурсивное сканирование всей папки: {target_path}...")
    
    # Ищем все файлы .cs во всех вложенных папках
    search_pattern = os.path.join(target_path, "**", "*.cs")
    cs_files = glob.glob(search_pattern, recursive=True)
    
    # Если файлов .cs нет, собираем общие текстовые исходники
    if not cs_files:
        search_pattern = os.path.join(target_path, "**", "*.*")
        cs_files = [f for f in glob.glob(search_pattern, recursive=True) if not os.path.isdir(f)]
        
    return cs_files

def run_ai_review(file_paths, criteria_text):
    """Сбор содержимого ВСЕХ файлов папки и отправка на анализ в Ollama"""
    code_contents = ""
    print(f"\n📂 Всего найдено файлов для анализа в папке: {len(file_paths)}")
    
    for fp in file_paths:
        # Пропускаем служебные папки и сборочные директории
        if any(skip in fp for skip in ['.git', 'bin', 'obj', '__pycache__', '.vs']):
            continue
            
        print(f"  📖 Чтение файла: {fp}")
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                code_contents += f"\n\n================ FILE: {fp} ================\n{f.read()}\n"
        except Exception as e:
            print(f"  ⚠️ Не удалось прочитать файл {fp}: {e}")

    prompt = f"""
Ты — строгий преподаватель по программированию на C#. 
Проверь проект студента (все файлы в папке) на соответствие требованиям из методички:

=== МЕТОДИЧКА И ЗАДАНИЯ КУРСА (RAG) ===
{criteria_text}
=========================================

Исходный код всех файлов проекта студента:
{code_contents}

Сформируй подробный отчёт в формате Markdown:
1. **Общая оценка проекта**: (от 1 до 5) и статус (зачтено / отправлено на доработку).
2. **Анализ по задачнику**: Проверь, какие классы и задачи из методички реализованы (например, Animal, Figure, ClassRoom, DocumentWorker, банкомат и т.д.) и есть ли ошибки.
3. **Рекомендации**: Конкретные замечания по структуре проекта.
4. **Примеры исправлений**: Исправленный код для ключевых проблемных мест.
"""

    print("\n🤖 Отправка всей кодовой базы модели qwen2.5 через Ollama...")
    response = client.chat.completions.create(
        model="qwen2.5",
        messages=[
            {"role": "system", "content": "Ты экспертный преподаватель и AI-ревьюер кода на C#."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    target_directory = sys.argv[1] if len(sys.argv) > 1 else "student_repo_sample"
    
    print(f"🚀 Запуск Master AI Reviewer для папки: {target_directory}")
    
    criteria = load_criteria()
    files = scan_target_directory(target_directory)
    
    if not files:
        print("❌ В указанной папке не найдено файлов для анализа!")
    else:
        report = run_ai_review(files, criteria)
        
        output_report = "PR_AI_Review_Report.md"
        with open(output_report, "w", encoding="utf-8") as out:
            out.write(report)
            
        print(f"\n✨ Успешно! Полный отчёт по всей папке сохранен в файл: {output_report}")
