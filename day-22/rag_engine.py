from __future__ import annotations
import os
import json
from typing import List, Dict, Any

class RAGEngine:
    def __init__(self, storage_dir: str = "index_storage_day21"):
        self.index_file = os.path.join(storage_dir, "vector_index.json")

    def load_index(self) -> Dict[str, Any]:
        if os.path.exists(self.index_file):
            with open(self.index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"chunks": []}

    def search_relevant_chunks(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Простой релевантный поиск чанков по совпадению ключевых слов (или эмбеддинг-заглушек)."""
        index_data = self.load_index()
        chunks = index_data.get("chunks", [])
        
        if not chunks:
            return []

        query_words = set(query.lower().split())
        scored_chunks = []

        for chunk in chunks:
            content = chunk.get("content", "").lower()
            section = chunk.get("section", "").lower()
            
            # Считаем простейший overlap слов для ранжирования
            score = sum(1 for word in query_words if word in content or word in section)
            scored_chunks.append((score, chunk))

        # Сортируем по релевантности (score по убыванию)
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        
        # Возвращаем top_k лучших чанков
        best_chunks = [chunk for score, chunk in scored_chunks[:top_k]]
        return best_chunks

    def generate_answer_without_rag(self, query: str) -> str:
        """Ответ модели БЕЗ RAG (только на «базовых знаниях» модели)."""
        # Здесь имитируется или вызывается LLM без контекста документов
        return (
            f"[Режим БЕЗ RAG]\n"
            f"Ответ сгенерирован на основе внутренней памяти модели без обращения к локальной базе документов. "
            f"В точных деталях по вашему уникальному файлу модель может ошибаться или выдумывать факты (галлюцинировать)."
        )

    def generate_answer_with_rag(self, query: str) -> Dict[str, Any]:
        """Ответ модели С RAG (поиск контекста + объединение с вопросом)."""
        relevant_chunks = self.search_relevant_chunks(query, top_k=3)
        
        if not relevant_chunks:
            return {
                "answer": "В локальном индексе не найдено подходящих документов для ответа на этот вопрос.",
                "sources": []
            }

        # Формируем контекст из найденных чанков
        context_blocks = []
        sources = set()
        for chunk in relevant_chunks:
            sources.add(f"{chunk['source']} (Тема: {chunk['section']})")
            context_blocks.append(f"--- Источник: {chunk['source']} [{chunk['section']}] ---\n{chunk['content']}")

        combined_context = "\n\n".join(context_blocks)

        # Формируем итоговый промпт для LLM
        prompt = f"""Используя ТОЛЬКО следующий контекст из документов, ответь на вопрос пользователя. Если в контексте нет ответа, так и скажи.

Контекст:
{combined_context}

Вопрос пользователя: {query}
"""

        # Эмулируем качественный ответ LLM на основе найденного контекста
        answer = (
            f"[Режим С RAG]\n"
            f"На основе найденных отрывков в вашей базе документов:\n\n"
            f"**Анализ контекста:** Найдено релевантных чанков: {len(relevant_chunks)}.\n"
            f"**Ответ:** [Сформирован точно по тексту чанков с опорой на разделы: {', '.join(sources)}]"
        )

        return {
            "answer": answer,
            "sources": list(sources),
            "retrieved_chunks": relevant_chunks
        }
