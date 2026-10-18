import os
import subprocess
import sys
from openai import OpenAI

def get_git_diff():
    try:
        subprocess.run(["git", "fetch", "origin", "main"], check=False)
        return subprocess.check_output(["git", "diff", "origin/main...HEAD"], text=True).strip()
    except:
        return subprocess.check_output(["git", "diff", "HEAD~1"], text=True).strip()

def generate_ai_review(diff_text):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url="https://llm.effective.land/v1")
    res = client.chat.completions.create(
        model="glm-4-flash",
        messages=[
            {"role": "system", "content": "Ты — старший архитектор. Проведи AI Code Review для git diff на русском языке."},
            {"role": "user", "content": f"Вот git diff:\n\n```diff\n{diff_text}\n```"}
        ],
        temperature=0.2
    )
    return res.choices[0].message.content

if __name__ == "__main__":
    diff = get_git_diff()
    if diff:
        print(generate_ai_review(diff))
