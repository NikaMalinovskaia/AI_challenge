#!/bin/bash

# Экспортируем ваш ключ LiteLLM
export LITELLM_API_KEY="ваш_ключ_сюда"

# Запускаем скрипт дня 4
python3 main_day4.py

echo "Эксперимент по температуре успешно завершен!"
