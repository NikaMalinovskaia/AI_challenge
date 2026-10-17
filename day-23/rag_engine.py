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

    def search_relevant_chunks(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Поиск чанков с расчетом метрики релевантности (score) на основе совпадения слов."""
        index_data = self.load_index()
        chunks = index_data.get("chunks", [])
        
        if not chunks:
            return []

        query_words = set(query.lower().split())
        scored_chunks = []

        for chunk in chunks:
            content = chunk.get("content", "").lower()
            section = chunk.get("section", "").lower()
            
            # Считаем количество совпадений слов и нормализуем в условный score от 0.0 до 1.0
            matches = sum(1 for word in query_words if word in content or word in section)
            score = float(matches) / max(len(query_words), 1)
            # Добавим небольшой базовый вес, чтобы чанки не занулялись полностью
            if matches > 0:
                score = max(score, 0.1)
            
            chunk_copy = chunk.copy()
            chunk_copy["score"] = round(score, 2)
            scored_chunks.append((score, chunk_copy))

        # Сортируем по убыванию score
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        
        best_chunks = [chunk for score, chunk in scored_chunks[:top_k]]
        return best_chunks
