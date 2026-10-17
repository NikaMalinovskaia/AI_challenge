#!/bin/bash

export LITELLM_API_KEY="ваш-ключ-сюда"
export LITELLM_API_BASE="https://llm.effective.land/v1"

# Используем только те модели, которые разрешены для вашего ключа
export MODEL_WEAK="glm-4.7-flash"
export MODEL_MEDIUM="minimax-m3"
export MODEL_STRONG="deepseek-v4-pro"

echo "Запуск скрипта эксперимента (main_day5.py)..."
python3 main_day5.py

if [ $? -ne 0 ]; then
    echo "❌ Ошибка: Эксперимент не удался. Отчеты не были созданы!"
    exit 1
fi

echo "🎉 Готово! Проверьте файлы answer_comparison.md и day5_metrics_report.md"
