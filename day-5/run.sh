#!/bin/bash

# Настройка переменных окружения (впишите ваш ключ сюда)
export LITELLM_API_KEY="your_litellm_api_key_here"
export LITELLM_API_BASE="https://api.litellm.ai" # или ваш корпоративный прокси

# Начало, середина и конец Hugging Face Hub (по версии популярных Instruct-моделей)
export MODEL_WEAK="huggingface/google/gemma-2-2b-it"              # Компактная (слабая)
export MODEL_MEDIUM="huggingface/mistralai/Mistral-7B-Instruct-v0.3" # Сбалансированная (средняя)
export MODEL_STRONG="huggingface/meta-llama/Meta-Llama-3-70B-Instruct" # Тяжелый флагман (сильная)

echo "⚙️ Проверка и установка зависимостей..."
pip3 install litellm openai python-dotenv --quiet

echo "▶️ Запуск скрипта эксперимента (main.py)..."
python3 main.py

echo "✨ Готово! Проверьте файлы answer_comparison.md и day5_metrics_report.md"
