from __future__ import annotations
import os
import json
import re
import urllib.request
import ssl
from document_indexer import DocumentIndexer
from rag_engine import RAGEngine

class IndexingAgentDay22:
    def __init__(self):
        self.indexer = DocumentIndexer()
        self.rag_engine = RAGEngine()
        self.api_key = "sk-L2Fx4Xsvy_OA6gcp3gG2pA"
        self.base_url = "https://llm.effective.land/v1"
        self.model_name = "glm-5.3-flash"

    def _call_llm(self, messages: list[dict], temperature: float = 0.3) -> str:
        """Вызов LLM через встроенный urllib с отключенной проверкой SSL-окружения."""
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=90) as response:
                response_body = response.read().decode("utf-8")
                resp_data = json.loads(response_body)
                
                if "choices" in resp_data and len(resp_data["choices"]) > 0:
                    return resp_data["choices"][0]["message"]["content"]
                elif "error" in resp_data:
                    raise RuntimeError(f"Ошибка API: {resp_data['error']}")
                else:
                    raise RuntimeError(f"Неизвестный формат ответа: {response_body}")
                    
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8") if e.fp else str(e)
            raise RuntimeError(f"HTTP ошибка LLM ({e.code}): {err_body}")
        except Exception as e:
            raise RuntimeError(f"Сетевая ошибка LLM (urllib): {e}")

    def generate_dynamic_benchmarks(self, documents: dict[str, str]) -> list[dict]:
        """Генерирует 10 контрольных вопросов с ожиданиями и источниками через LLM."""
        if not documents:
            return []
        
        combined_text = ""
        for name, text in documents.items():
            combined_text += f"\n--- Файл: {name} ---\n{text[:4000]}"
            
        default_source = list(documents.keys())[0] if documents else "doc.txt"
        
        prompt = f"""Внимательно прочитай текст документа и составь ровно 10 глубоких контрольных вопросов по его содержанию.
Для каждого вопроса укажи:
1. question: сам вопрос.
2. expectation: ожидаемый содержательный ответ (что должно быть в ответе).
3. expected_sources: массив с именем файла-источника (например, ["{default_source}"]).

Верни результат СТРОГО в виде JSON-массива без какого-либо дополнительного текста, без блоков кода ```json.

Формат элемента:
[
  {{
    "id": 1,
    "question": "Вопрос по тексту?",
    "expectation": "Что должно быть в ответе",
    "expected_sources": ["{default_source}"]
  }}
]

Текст документов:
{combined_text}
"""
        messages = [
            {"role": "system", "content": "Ты эксперт по оценке качества RAG. Возвращай только чистый валидный JSON-массив."},
            {"role": "user", "content": prompt}
        ]
        
        response_text = self._call_llm(messages, temperature=0.5)
        
        clean_json = response_text.strip()
        clean_json = re.sub(r"^```json\s*", "", clean_json, flags=re.IGNORECASE)
        clean_json = re.sub(r"^```\s*", "", clean_json)
        clean_json = re.sub(r"\s*```$", "", clean_json).strip()
        
        start_idx = clean_json.find('[')
        end_idx = clean_json.rfind(']')
        
        if start_idx != -1 and end_idx != -1:
            json_str = clean_json[start_idx:end_idx+1]
            benchmarks = json.loads(json_str)
            if isinstance(benchmarks, list) and len(benchmarks) > 0:
                self.save_benchmarks_to_index(benchmarks)
                return benchmarks
                
        raise ValueError(f"Не удалось распарсить JSON бенчмарков: {response_text}")

    def save_benchmarks_to_index(self, benchmarks: list[dict]):
        index_data = self.indexer.load_index()
        index_data["benchmarks"] = benchmarks
        with open(self.indexer.index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

    def get_test_benchmarks(self) -> list[dict]:
        index_data = self.indexer.load_index()
        return index_data.get("benchmarks", [])

    def run_indexing(self, documents: dict[str, str], strategy: str) -> str:
        if not documents:
            return "⚠️ Ошибка: Нет документов для индексации."
        
        # Сохраняем ранее сгенерированные бенчмарки, чтобы они не затирались при смене стратегии
        old_benchmarks = self.get_test_benchmarks()
        
        total = self.indexer.build_and_save_index(documents, strategy=strategy)
        
        # Восстанавливаем бенчмарки в новом индексе
        if old_benchmarks:
            self.save_benchmarks_to_index(old_benchmarks)
            
        return f"✅ Успешно проиндексировано! Создано чанков: {total} (стратегия: `{strategy}`)."

    def generate_answer_without_rag(self, query: str) -> str:
        messages = [
            {"role": "system", "content": "Ты полезный ассистент."},
            {"role": "user", "content": query}
        ]
        try:
            return self._call_llm(messages, temperature=0.3)
        except Exception as e:
            return f"⚠️️ Ошибка LLM: {e}"

    def generate_answer_with_rag(self, query: str) -> dict:
        relevant_chunks = self.rag_engine.search_relevant_chunks(query, top_k=3)
        if not relevant_chunks:
            return {
                "answer": "В локальной базе документов не найдено релевантной информации.",
                "sources": [],
                "retrieved_chunks": []
            }

        sources = set()
        context_blocks = []
        for chunk in relevant_chunks:
            src_name = chunk.get('source', 'doc.txt')
            sec = chunk.get('section', 'блок')
            sources.add(f"{src_name} ({sec})")
            context_blocks.append(f"Источник: {src_name} [{sec}]\n{chunk['content']}")

        joined_context = "\n\n".join(context_blocks)

        prompt = f"""Используй ТОЛЬКО приведенный ниже контекст из документов, чтобы ответить на вопрос пользователя. Если в контексте нет ответа, честно скажи об этом.

Контекст:
{joined_context}

Вопрос пользователя: {query}
Ответ:"""

        messages = [
            {"role": "system", "content": "Ты строгий ассистент по работе с документами. Отвечай только на основе предоставленного контекста."},
            {"role": "user", "content": prompt}
        ]

        try:
            answer = self._call_llm(messages, temperature=0.1)
        except Exception as e:
            answer = f"⚠️ Ошибка LLM: {e}"

        return {
            "answer": answer,
            "sources": list(sources),
            "retrieved_chunks": relevant_chunks
        }
