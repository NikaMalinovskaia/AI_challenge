import http.server
import socketserver
import json
import requests
import threading
import webbrowser

PORT = 8080
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5"

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Локальный AI Код-Ревьювер (C#)</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f4f4f9; color: #333; }
        .container { max-width: 800px; margin: auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        textarea { width: 100%; height: 150px; padding: 12px; border: 1px solid #ccc; border-radius: 4px; font-family: monospace; font-size: 14px; }
        button { background: #007bff; color: white; border: none; padding: 12px 20px; font-size: 16px; border-radius: 4px; cursor: pointer; margin-top: 10px; }
        button:hover { background: #0056b3; }
        pre { background: #eef; padding: 15px; border-radius: 4px; white-space: pre-wrap; font-family: monospace; }
        .loading { color: #888; font-style: italic; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🚀 Локальный AI Код-Ревьювер C# (Ollama / Qwen 2.5)</h2>
        <p>Приложение работает полностью локально без облачных API.</p>
        <textarea id="codeinput" placeholder="Вставьте код на C# здесь...">public class Account {
    public decimal balance;
}</textarea><br>
        <button onclick="sendCode()">Проверить код</button>
        <h3>Результат ревью:</h3>
        <pre id="result">Ожидание ввода...</pre>
    </div>

    <script>
        async function sendCode() {
            const code = document.getElementById('codeinput').value;
            const resultPre = document.getElementById('result');
            resultPre.className = "loading";
            resultPre.innerText = "🔄 Анализируем код локальной моделью...";

            try {
                const response = await fetch('/review', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code: code })
                });
                const data = await response.json();
                resultPre.className = "";
                resultPre.innerText = data.result;
            } catch (error) {
                resultPre.className = "";
                resultPre.innerText = "Ошибка соединения с локальным сервером: " + error;
            }
        }
    </script>
</body>
</html>
"""

class ReviewHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode("utf-8"))

    def do_POST(self):
        if self.path == '/review':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            req_json = json.loads(post_data.decode('utf-8'))
            code_snippet = req_json.get("code", "")

            prompt = (
                "Ты — строгий преподаватель и эксперт по ООП в C#. "
                "Проведи код-ревью следующего кода, найди нарушения инкапсуляции и дай рекомендации:\n\n"
                f"```csharp\n{code_snippet}\n```\n\n"
                "Структура ответа:\n1. Замечания\n2. Оценка\n3. Рекомендации"
            )

            payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}
            
            try:
                resp = requests.post(OLLAMA_URL, json=payload, timeout=90)
                if resp.status_code == 200:
                    ai_response = resp.json().get("response", "").strip()
                else:
                    ai_response = f"Ошибка Ollama API: {resp.status_code}"
            except Exception as e:
                ai_response = f"Ошибка подключения к локальному серверу: {e}"

            response_data = {"result": ai_response}
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode("utf-8"))

if __name__ == "__main__":
    url = f"http://localhost:{PORT}"
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    
    with socketserver.TCPServer(("", PORT), ReviewHandler) as httpd:
        print(f"🌐 Веб-приложение запущенно! Автоматически открываю: {url}")
        httpd.serve_forever()
