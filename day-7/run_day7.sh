#!/bin/bash

# Экспортируем ключ
export LITELLM_API_KEY="YOUR_KEY"

echo "Запуск агента (День 7)..."
python3 main_day7.py

# Проверяем код возврата Python ($?)
if [ $? -eq 0 ]; then
    echo "День 7 успешно выполнен!"
else
    echo "День 7 завершился с ошибкой!"
    exit 1
fi
