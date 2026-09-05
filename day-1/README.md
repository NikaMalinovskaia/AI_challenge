# AI Challenge - Day 1

 # DeepSeek Python CLI

Небольшой скрипт на Python, который отправляет промпт в корпоративный LLM API через LiteLLM и печатает ответ в консоль.

## Требования

- Python 3.9+
- Библиотека `openai`
- Корпоративный API-ключ LiteLLM

## Конфигурация

Приложение читает API-ключ из переменной окружения:

```bash
export LITELLM_API_KEY=<ваш LiteLLM API key>

По умолчанию в коде используется:
API Base URL: https://llm.effective.land/v1
Model: deepseek-v4-flash-0731

## Запуск
Перейди в папку с проектом и запусти скрипт:

python3 main.py

## Дополнительные параметры

В файле main.py вы можете гибко настраивать параметры запроса:
Выбор модели (deepseek-v4-flash-0731, deepseek-v4-pro, glm-4.7-flash и др.)
Параметр temperature для настройки креативности ответов
Системный промпт и текст сообщения пользователя (messages)
