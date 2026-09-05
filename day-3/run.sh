#!/bin/bash

# Экспортируем ваш LiteLLM ключ
export LITELLM_API_KEY="ваш_ключ_сюда"

# Запускаем Python-скрипт (библиотека openai должна быть установлена: pip install openai)
python3 main.py

echo "Все результаты записаны в answer_comparison.md"
