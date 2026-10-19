import os
import sys
import glob
import json
import subprocess
from urllib.parse import urlparse
from openai import OpenAI
from prompts import SYSTEM_PROMPT, get_review_prompt

def load_config():
    """Загрузка конфигурации из config.json"""
    config_path = "config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Ошибка чтения config.json: {e}")
    # Дефолтные настройки, если файла нет
    return {
        "ollama_base_url": "http://localhost:11434/v1",
        "ollama_model": "qwen2.5",
        "api_key": "ollama",
        "ignored_directories": [".git", "bin", "obj", "__pycache__", ".vs"],
        "criteria_file": "criteria.md"
    }

# Загружаем конфигурацию
config = load_config()

# Инициализация клиента Ollama через параметры конфига
client = OpenAI(
    base_url=config["ollama_base_url"],
    api_key=config["api_key"]
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
    """Загрузка методички с критериями оценки (RAG)"""
    criteria_path = config["criteria_file"]
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
    Динамический хендлер целей: разбирает ссылки GitHub или локальные пути.
    """
    if "github.com" in target_arg:
        print_colored(f"🌐 Анализируем GitHub ссылку: {target_arg}", Colors.HEADER)
        
        parsed_url = urlparse(target_arg)
        path_segments = [seg for seg in parsed_url.path.split("/") if seg]
        
        if len(path_segments) < 2:
            print_colored("❌ Некорректная ссылка на GitHub.", Colors.FAIL)
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
            print_colored(f"📁 Папка {local_dir} существует. Выполняем git pull...", Colors.GREEN)
            try:
                subprocess.run(["git", "-C", local_dir, "pull"], check=True)
            except Exception as e:
                print_colored(f"⚠️ Не удалось обновить через git pull: {e}", Colors.WARNING)
        else:
            print_colored(f"📦 Клонируем репозиторий {base_repo_url}...", Colors.GREEN)
            try:
                subprocess.run(["git", "clone", base_repo_url, local_dir], check=True)
            except Exception as e:
                print_colored(f"❌ Ошибка клонирования: {e}", Colors.FAIL)
                sys.exit(1)
                
        final_path = os.path.join(local_dir, *sub_folder_parts) if sub_folder_parts else local_dir
        sub_suffix = f"_{'_'.join(sub_folder_parts)}" if sub_folder_parts else ""
        report_filename = f"Review_Report_{repo_name}{sub_suffix}.md"
        
        return final_path, report_filename
    else:
        local_path = target_arg
        folder_base_name = os.path.basename(os.path.normpath(local_path)) or "local_project"
        report_filename = f"Review_Report_{folder_base_name}.md"
        return local_path, report_filename

def scan_target_directory(target_path):
    """Рекурсивное сканирование папки с исключением системных директорий"""
    if not os.path.exists(target_path):
        print_colored(f"❌ Ошибка: Путь не существует -> {target_path}", Colors.FAIL)
        return []
    
    print_colored(f"🔍 Сканирование директории: {target_path}...", Colors.GREEN)
    search_pattern = os.path.join(target_path, "**", "*.cs")
    cs_files = glob.glob(search_pattern, recursive=True)
    
    if not cs_files:
        search_pattern = os.path.join(target_path, "**", "*.*")
        cs_files = [f for f in glob.glob(search_pattern, recursive=True) if not os.path.isdir(f)]
        
    return cs_files

def run_ai_review(file_paths, criteria_text):
    """Сбор кодовой базы и выполнение инференса через локальную модель"""
    code_contents = ""
    print_colored(f"\n📂 Найдено файлов для анализа: {len(file_paths)}", Colors.HEADER)
    
    ignored = tuple(config["ignored_directories"])
    for fp in file_paths:
        if any(skip in fp for skip in ignored):
            continue
            
        print_colored(f"  📖 Чтение файла: {fp}", Colors.BLUE)
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                code_contents += f"\n\n================ FILE: {fp} ================\n{f.read()}\n"
        except Exception as e:
            print_colored(f"  ⚠️ Не удалось прочитать файл {fp}: {e}", Colors.WARNING)

    # Получаем изолированный промпт из модуля prompts.py
    prompt = get_review_prompt(criteria_text, code_contents)

    print_colored(f"\n🤖 Отправка кодовой базы модели {config['ollama_model']} через Ollama...", Colors.HEADER)
    response = client.chat.completions.create(
        model=config["ollama_model"],
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
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
    print_colored(f"🚀 Запуск Master AI Reviewer (Harness) для цели: {raw_target}", Colors.HEADER)
    
    target_directory, output_report = prepare_target(raw_target)
    
    criteria = load_criteria()
    files = scan_target_directory(target_directory)
    
    if not files:
        print_colored("❌ В указанной директории не найдено файлов для анализа!", Colors.FAIL)
    else:
        report = run_ai_review(files, criteria)
        
        with open(output_report, "w", encoding="utf-8") as out:
            out.write(report)
            
        print_colored(f"\n✨ Успешно! Модульный отчёт сохранен в файл: {output_report}", Colors.GREEN)
