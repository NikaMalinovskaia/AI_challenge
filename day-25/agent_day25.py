from __future__ import annotations
import os
import json
import re
import urllib.request
import ssl
from document_indexer import DocumentIndexer
from rag_engine import RAGEngine

class IndexingAgentDay25:
    def __init__(self):
        self.indexer = DocumentIndexer()
        self.rag_engine = RAGEngine()
        self.api_key = "sk-L2Fx4Xsvy_OA6gcp3gG2pA"
        self.base_url = "https://llm.effective.land/v1"
        self.model_name = "glm-5.3-flash"

    def _call_llm(self, messages: list[dict], temperature: float = 0.3) -> str:
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
        except Exception as e:
            raise RuntimeError(f"Сетевая ошибка LLM: {e}")

    def update_task_state(self, history: list[dict], current_query: str, current_state: dict) -> dict:
        """Динамически обновляет память задачи (цель, ограничения, зафиксированные термины)."""
        history_snippet = "\n".join([f"{m['role']}: {m['content']}" for m in history[-6:]])
        
        prompt = f"""Проанализируй историю диалога и текущий вопрос пользователя. Обнови состояние задачи (Task State) в формате JSON.

Текущее состояние задачи:
{json.dumps(current_state, ensure_ascii=False)}

Последние сообщения диалога:
{history_snippet}

Новый вопрос пользователя: {current_query}

Верни СТРОГО валидный JSON (без блоков кода ```json) следующей структуры:
{{
  "goal": "Главная текущая цель пользователя в диалоге",
  "constraints": ["ограничение 1", "ограничение 2"],
  "terms": ["ключевой термин 1", "термин 2"],
  "progress": "Краткий статус выполнения задачи"
}}
"""
        messages = [
            {"role": "system", "content": "Ты модуль управления состоянием задачи (Task State Manager). Возвращай только чистый JSON."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            resp = self._call_llm(messages, temperature=0.1).strip()
            clean_json = re.sub(r"^```json\s*", "", resp, flags=re.IGNORECASE)
            clean_json = re.sub(r"^```\s*", "", clean_json)
            clean_json = re.sub(r"\s*```$", "", clean_json).strip()
            
            start_idx = clean_json.find('{')
            end_idx = clean_json.rfind('}')
            if start_idx != -1 and end_idx != -1:
                return json.loads(clean_json[start_idx:end_idx+1])
        except Exception:
            pass
        return current_state

    def contextual_query_rewrite(self, query: str, history: list[dict]) -> str:
        """Переформулирует запрос с учетом истории диалога для точного векторного поиска."""
        history_snippet = "\n".join([f"{m['role']}: {m['content']}" for m in history[-4:]])
        prompt = f"""Учитывая историю диалога ниже, перепиши последний вопрос пользователя в самостоятельный поисковый запрос, понятный вне контекста беседы. Выдай ТОЛЬКО переписанный запрос.

История диалога:
{history_snippet}

Последний вопрос: {query}
Самостоятельный поисковый запрос:"""
        
        messages = [
            {"role": "system", "content": "Ты модуль разрешения местоимений и оптимизации поисковых запросов."},
            {"role": "user", "content": prompt}
        ]
        try:
            rewritten = self._call_llm(messages, temperature=0.1).strip()
            return rewritten if rewritten else query
        except Exception:
            return query

    def generate_chat_response(
        self, 
        query: str, 
        history: list[dict], 
        task_state: dict,
        top_k_initial: int = 5, 
        top_k_final: int = 3, 
        threshold: float = 0.1, 
        use_filter: bool = True
    ) -> tuple[dict, dict]:
        
        # 1. Обновляем память задачи
        updated_state = self.update_task_state(history, query, task_state)

        # 2. Переписываем запрос с учетом истории
        processed_query = self.contextual_query_rewrite(query, history)

        # 3. RAG поиск
        raw_chunks = self.rag_engine.search_relevant_chunks(processed_query, top_k=top_k_initial)
        
        if not raw_chunks:
            return {
                "answer": "Я не знаю ответа на этот вопрос, так как в базе документов нет релевантной информации. Пожалуйста, уточните ваш запрос.",
                "sources": [],
                "quotes": [],
                "rewritten_query": processed_query,
                "is_i_dont_know": True
            }, updated_state

        filtered_chunks = []
        for chunk in raw_chunks:
            score = chunk.get("score", 1.0)
            if use_filter and score < threshold:
                continue
            filtered_chunks.append(chunk)

        final_chunks = filtered_chunks[:top_k_final]

        if not final_chunks:
            return {
                "answer": "Я не знаю ответа на этот вопрос, так как найденные фрагменты не достигают необходимого порога релевантности. Пожалуйста, уточните или переформулируйте запрос.",
                "sources": [],
                "quotes": [],
                "rewritten_query": processed_query,
                "is_i_dont_know": True
            }, updated_state

        # 4. Формирование контекста
        sources_info = []
        context_blocks = []
        for idx, chunk in enumerate(final_chunks):
            src_name = chunk.get('source', 'doc.txt')
            sec = chunk.get('section', 'блок')
            chunk_id = chunk.get('chunk_id', idx)
            source_tag = f"{src_name} (раздел: {sec}, ID: {chunk_id})"
            sources_info.append(source_tag)
            context_blocks.append(f"[{source_tag}]\n{chunk['content']}")

        joined_context = "\n\n".join(context_blocks)
        history_snippet = "\n".join([f"{m['role']}: {m['content']}" for m in history[-6:]])

        prompt = f"""Ты интеллектуальный ассистент с доступом к базе знаний и памятью задачи.
Текущая цель задачи: {updated_state.get('goal', 'Не задана')}
Зафиксированные термины: {', '.join(updated_state.get('terms', []))}

История диалога:
{history_snippet}

Контекст из документов для текущего вопроса:
{joined_context}

Вопрос пользователя: {query}

Инструкции:
1. Отвечай на вопрос, используя историю и контекст.
2. Если в контексте нет ответа, отвечай ровно фразой: "Я не знаю."
3. Указывай источники и точные короткие цитаты.
"""
        messages = [
            {"role": "system", "content": "Ты надежный RAG-ассистент с памятью диалога."},
            {"role": "user", "content": prompt}
        ]

        try:
            answer = self._call_llm(messages, temperature=0.2)
        except Exception as e:
            answer = f"⚠️ Ошибка LLM: {e}"

        quotes = [chunk.get("content")[:250] + "..." for chunk in final_chunks]

        return {
            "answer": answer,
            "sources": sources_info,
            "quotes": quotes,
            "rewritten_query": processed_query,
            "is_i_dont_know": False
        }, updated_state
