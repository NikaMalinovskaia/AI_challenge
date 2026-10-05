from __future__ import annotations
import os
import json
import io
from typing import List, Dict, Any
from pypdf import PdfReader

class DocumentIndexer:
    def __init__(self, storage_dir: str = "index_storage_day21"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        self.index_file = os.path.join(self.storage_dir, "vector_index.json")

    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        """Извлекает текст из байтов PDF-файла с помощью pypdf."""
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            text = ""
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n\n--- Страница {page_num + 1} ---\n\n" + page_text
            return text
        except Exception as e:
            return f"[Ошибка чтения PDF: {e}]"

    def _generate_smart_title(self, text_content: str, fallback_title: str) -> str:
        """Генерирует смысловой заголовок отрывка на основе его содержимого."""
        clean_text = text_content.strip()
        if not clean_text:
            return fallback_title
        
        # Берем первые 5-6 слов отрывка для формирования емкой темы
        words = clean_text.split()
        if len(words) >= 5:
            preview = " ".join(words[:5]) + "..."
            return f"Тема: {preview}"
        return fallback_title

    def chunk_by_fixed_size(self, text: str, source: str, chunk_size: int = 300, overlap: int = 50) -> List[Dict[str, Any]]:
        """Стратегия 1: Чанкинг по фиксированному размеру символов с перекрытием."""
        chunks = []
        text_length = len(text)
        start = 0
        chunk_id = 0

        while start < text_length:
            end = min(start + chunk_size, text_length)
            chunk_text = text[start:end]
            
            meta = {
                "chunk_id": f"fixed_{chunk_id}",
                "source": source,
                "strategy": "fixed_size",
                "section": f"Символы {start}-{end}",
                "content": chunk_text,
                "embedding_stub": [float(ord(c) % 10) / 10.0 for c in chunk_text[:10]]
            }
            chunks.append(meta)
            chunk_id += 1
            start += chunk_size - overlap

        return chunks

    def chunk_by_structure(self, text: str, source: str) -> List[Dict[str, Any]]:
        """Стратегия 2: Структурный чанкинг с умными заголовками отрывков."""
        chunks = []
        
        if "--- Страница" in text:
            sections = text.split("--- Страница ")
        else:
            sections = text.split("\n\n")

        for idx, section in enumerate(sections):
            section_content = section.strip()
            if not section_content:
                continue
            
            if "--- Страница" in text and idx > 0:
                lines = section_content.split("\n")
                page_num = lines[0].split(" ---")[0]
                section_content = "\n".join(lines[1:]).strip()
                fallback = f"Страница {page_num}"
            else:
                fallback = f"Блок {idx}"

            if not section_content:
                continue

            # Генерируем смысловой заголовок о чем этот отрывок
            smart_title = self._generate_smart_title(section_content, fallback)

            chunk_id = f"struct_{idx}"
            meta = {
                "chunk_id": chunk_id,
                "source": source,
                "strategy": "structural",
                "section": smart_title,
                "content": section_content,
                "embedding_stub": [float(ord(c) % 7) / 7.0 for c in section_content[:10]]
            }
            chunks.append(meta)

        return chunks

    def build_and_save_index(self, documents: Dict[str, str], strategy: str = "fixed_size") -> int:
        all_chunks = []
        for source, text in documents.items():
            if strategy == "fixed_size":
                chunks = self.chunk_by_fixed_size(text, source)
            elif strategy == "structural":
                chunks = self.chunk_by_structure(text, source)
            else:
                raise ValueError(f"Неизвестная стратегия: {strategy}")
            all_chunks.extend(chunks)

        index_data = {
            "strategy": strategy,
            "total_chunks": len(all_chunks),
            "chunks": all_chunks
        }

        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

        return len(all_chunks)

    def compare_strategies(self, documents: Dict[str, str]) -> Dict[str, Any]:
        fixed_chunks = []
        struct_chunks = []
        for source, text in documents.items():
            fixed_chunks.extend(self.chunk_by_fixed_size(text, source))
            struct_chunks.extend(self.chunk_by_structure(text, source))
            
        return {
            "fixed_size": {"total_chunks": len(fixed_chunks), "chunks": fixed_chunks},
            "structural": {"total_chunks": len(struct_chunks), "chunks": struct_chunks}
        }

    def load_index(self) -> Dict[str, Any]:
        if os.path.exists(self.index_file):
            with open(self.index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"strategy": "none", "total_chunks": 0, "chunks": []}
