import os
import argparse
import json
import sys
from openai import OpenAI

# Инициализация клиента для корпоративного LiteLLM API
client = OpenAI(
    api_key=os.environ["LITELLM_API_KEY"],
    base_url="https://llm.effective.land/v1",
)

MODEL_NAME = "deepseek-v4-flash-0731"

def main():
    parser = argparse.ArgumentParser(description="AI Challenge Day 2: Format & Control (Python)")
    parser.add_argument(
        "--mode", 
        choices=["free", "controlled"], 
        default="free",
        help="Режим: free (свободный ответ) или controlled (строгий JSON с валидацией)"
    )
    parser.add_argument(
        "--prompt", 
        default="",
        help="Запрос для модели (если не задан, читается из stdin)"
    )
    
    args = parser.parse_args()

    # Если промпт не передан через аргумент, пробуем прочитать его из stdin (как у коллеги на Go)
    prompt = args.prompt.strip()
    if not prompt:
        if not sys.stdin.isatty():
            prompt = sys.stdin.read().strip()
    
    # Если промпт всё еще пустой, ставим дефолтный или ругаемся
    if not prompt:
        prompt = "Напиши рецепт приготовления сырников"

    if args.mode == "free":
        print(f"=== РЕЖИМ: FREE (Запрос: {prompt}) ===")
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Ты полезный кулинарный ассистент."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        print(response.choices[0].message.content)

    elif args.mode == "controlled":
        print(f"=== РЕЖИМ: CONTROLLED (Strict JSON & Type Validation) ===")
        
        system_prompt = (
            "Ты API-сервис. Отвечай СТРОГО в формате валидного JSON-массива объектов с полями: "
            "name (строка — имя ингредиента), weight (строка — вес/объем), step_order (целое число — порядок в блюде). "
            "Не пиши никаких мыслей, рассуждений, вводного текста или марккода (типа ```json), только чистый JSON."
        )

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=2000,
        )
        
        raw_answer = response.choices[0].message.content
        
        if not raw_answer:
            print("Ошибка: Модель вернула пустой контент (None). Попробуй запустить еще раз.")
            exit(1)
        
        # Глубокая валидация и очистка (как у однокурсника)
        try:
            cleaned_answer = raw_answer.strip().removeprefix("```json").removesuffix("```").strip()
            parsed_json = json.loads(cleaned_answer)
            
            # 1. Проверяем, что корень — это массив
            if not isinstance(parsed_json, list):
                raise ValueError("Корневой элемент JSON должен быть массивом (list)")
            
            # 2. Проверяем типы каждого поля внутри элементов массива (глубокая валидация)
            for i, item in enumerate(parsed_json):
                if not isinstance(item, dict):
                    raise ValueError(f"Элемент с индексом {i} не является объектом (dict)")
                
                # Проверяем наличие и типы ключей
                if "name" not in item or not isinstance(item["name"], str):
                    raise ValueError(f"Элемент {i}: поле 'name' обязательное и должно быть строкой")
                if "weight" not in item or not isinstance(item["weight"], str):
                    raise ValueError(f"Элемент {i}: поле 'weight' обязательное и должно быть строкой")
                if "step_order" not in item or not isinstance(item["step_order"], int):
                    raise ValueError(f"Элемент {i}: поле 'step_order' обязательное и должно быть числом (int)")

            # Если всё прошло успешно — выводим отформатированный JSON
            print(json.dumps(parsed_json, ensure_ascii=False, indent=2))
            
        except (json.JSONDecodeError, ValueError) as e:
            print("Ошибка: Ответ модели не прошел строгую валидацию структуры!")
            print("Детали ошибки:", e)
            print("Сырой ответ от модели:\n", raw_answer)
            exit(1)

if __name__ == "__main__":
    main()
