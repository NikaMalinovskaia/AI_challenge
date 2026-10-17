import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["LITELLM_API_KEY"],
    base_url="https://llm.effective.land/v1",
)

response = client.chat.completions.create(
    model="deepseek-v4-flash-0731",
    messages=[
        {"role": "system", "content": "Ты полезный ассистент."},
        {"role": "user", "content": "Привет! Напиши коротко, что такое юнит-тест."},
    ],
    temperature=0.2,
)

print(response.choices[0].message.content)
