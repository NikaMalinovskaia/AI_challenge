#!/bin/bash

# Экспортируем ключ
export LITELLM_API_KEY="sk-L2Fx4Xsvy_OA6gcp3gG2pA"

echo "Запуск агента (День 6)..."
python3 main_day6.py

# Проверяем код возврата Python ($?)
if [ $? -eq 0 ]; then
    echo "День 6 успешно выполнен!"
else
    echo "День 6 завершился с ошибкой!"
    exit 1
fi
