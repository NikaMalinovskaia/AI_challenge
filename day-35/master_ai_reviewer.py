import os
import sys
import glob
import subprocess
from urllib.parse import urlparse
from openai import OpenAI

# Инициализация локального клиента Ollama
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

# ANSI-цвета для красивого вывода в терминале
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_colored(text, color=Colors.BLUE):
    print(f"{color}{text}{Colors.ENDC}")

def load_criteria():
    """Загрузка методички с критериями оценки из criteria.md (RAG)"""
    criteria_path = "criteria.md"
    if os.path.exists(criteria_path):
        print_colored(f"📚 Загрузка базы знаний (методички): {criteria_path}...", Colors.GREEN)
        try:
            with open(criteria_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print_colored(f"⚠️ Не удалось прочитать {criteria_path}: {e}", Colors.WARNING)
    return "Проверь инкапсуляцию, именование по стандартам C# и логику работы."

def prepare_target(target_arg):
    """
    Динамически разбирает любую ссылку GitHub (с произвольными именами репозиториев и папок) 
    или принимает локальный путь. Возвращает кортеж: (путь к папке, имя для отчёта).
    """
    if "github.com" in target_arg:
        print_colored(f"🌐 Анализируем GitHub ссылку: {target_arg}", Colors.HEADER)
        
        parsed_url = urlparse(target_arg)
        path_segments = [seg for seg in parsed_url.path.split("/") if seg]
        
        if len(path_segments) < 2:
            print_colored("❌ Некорректная ссылка на GitHub. Укажите полный путь к репозиторию или папке.", Colors.FAIL)
            sys.exit(1)
            
        owner = path_segments[0]
        repo_name = path_segments[1].replace(".git", "")
        
        base_repo_url = f"https://github.com/{owner}/{repo_name}.git"
        local_dir = f"temp_repo_{repo_name}"
        
        sub_folder_parts = []
        if "tree" in path_segments:
            tree_index = path_segments.index("tree")
            if len(path_segments) > tree_index + 2:
                sub_folder_parts = path_segments[tree_index + 2:]

        if os.path.exists(local_dir):
            print_colored(f"📁 Папка {local_dir} уже существует. Обновляем репозиторий (git pull)...", Colors.GREEN)
            try:
                subprocess.run(["git", "-C", local_dir, "pull"], check=True)
            except Exception as e:
                print_colored(f"⚠️ Не удалось обновить git pull: {e}", Colors.WARNING)
        else:
            print_colored(f"📦 Клонируем репозиторий {base_repo_url}...", Colors.GREEN)
            try:
                subprocess.run(["git", "clone", base_repo_url, local_dir], check=True)
            except Exception as e:
                print_colored(f"❌ Ошибка при клонировании репозитория: {e}", Colors.FAIL)
                sys.exit(1)
                
        final_path = os.path.join(local_dir, *sub_folder_parts) if sub_folder_parts else local_dir
        
        # Формируем уникальное имя отчёта на базе репозитория и подпапки (если есть)
        sub_suffix = f"_{'_'.join(sub_folder_parts)}" if sub_folder_parts else ""
        report_filename = f"Review_Report_{repo_name}{sub_suffix}.md"
        
        return final_path, report_filename
    else:
        # Для локальных папок
        local_path = target_arg
        folder_base_name = os.path.basename(os.path.normpath(local_path)) or "local_project"
        report_filename = f"Review_Report_{folder_base_name}.md"
        return local_path, report_filename

def scan_target_directory(target_path):
    if not os.path.exists(target_path):
        print_colored(f"❌ Ошибка: Путь не существует -> {target_path}", Colors.FAIL)
        return []
    
    print_colored(f"🔍 Рекурсивное сканирование целевой папки: {target_path}...", Colors.GREEN)
    search_pattern = os.path.join(target_path, "**", "*.cs")
    cs_files = glob.glob(search_pattern, recursive=True)
    
    if not cs_files:
        search_pattern = os.path.join(target_path, "**", "*.*")
        cs_files = [f for f in glob.glob(search_pattern, recursive=True) if not os.path.isdir(f)]
        
    return cs_files

def run_ai_review(file_paths, criteria_text):
    code_contents = ""
    print_colored(f"\n📂 Найдено файлов для анализа: {len(file_paths)}", Colors.HEADER)
    
    for fp in file_paths:
        if any(skip in fp for skip in ['.git', 'bin', 'obj', '__pycache__', '.vs']):
            continue
            
        print_colored(f"  📖 Чтение файла: {fp}", Colors.BLUE)
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                code_contents += f"\n\n================ FILE: {fp} ================\n{f.read()}\n"
        except Exception as e:
            print_colored(f"  ⚠️ Не удалось прочитать файл {fp}: {e}", Colors.WARNING)

    prompt = f"""
Ты — строгий преподаватель по программированию на C#. 
Проверь проект студента на соответствие требованиям из методички:

=== МЕТОДИЧКА И ЗАДАНИЯ КУРСА (RAG) ===
{criteria_text}
=========================================

Исходный код всех файлов проекта студента:
{code_contents}

Сформируй подробный отчёт в формате Markdown:
1. **Общая оценка проекта**: (от 1 до 5) и статус (зачтено / отправлено на доработку).
2. **Анализ по задачнику**: Проверь, какие классы и задачи из методички реализованы (Animal, Figure, ClassRoom, DocumentWorker и т.д.) и есть ли ошибки.
3. **Рекомендации**: Конкретные замечания по структуре проекта.
4. **Примеры исправлений**: Исправленный код для ключевых проблемных мест.
"""

    print_colored("\n🤖 Отправка кодовой базы модели qwen2.5 через Ollama...", Colors.HEADER)
    response = client.chat.completions.create(
        model="qwen2.5",
        messages=[
            {"role": "system", "content": "Ты экспертный преподаватель и AI-ревьюер кода на C#."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_colored("❌ Укажите путь к папке или ссылку на GitHub в качестве аргумента!", Colors.FAIL)
        print_colored("Пример: python3 master_ai_reviewer.py https://github.com/NikaMalinovskaia/AI_challenge/tree/main/test", Colors.WARNING)
        sys.exit(1)
        
    raw_target = sys.argv[1]
    print_colored(f"🚀 Запуск Master AI Reviewer для цели: {raw_target}", Colors.HEADER)
    
    # Динамически получаем путь и уникальное имя отчёта
    target_directory, output_report = prepare_target(raw_target)
    
    criteria = load_criteria()
    files = scan_target_directory(target_directory)
    
    if not files:
        print_colored("❌ В указанной директории не найдено файлов для анализа!", Colors.FAIL)
    else:
        report = run_ai_review(files, criteria)
        
        with open(output_report, "w", encoding="utf-8") as out:
            out.write(report)
            
        print_colored(f"\n✨ Успешно! Уникальный отчёт сохранен в файл: {output_report}", Colors.GREEN)
