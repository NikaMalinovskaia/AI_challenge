from __future__ import annotations
import os
from document_indexer import DocumentIndexer

class IndexingAgentDay21:
    def __init__(self):
        self.indexer = DocumentIndexer()

    def run_indexing(self, documents: dict[str, str], strategy: str) -> str:
        if not documents:
            return "⚠️ Ошибка: Нет документов для индексации. Загрузите файлы."
        total = self.indexer.build_and_save_index(documents, strategy=strategy)
        return f"✅ Успешно проиндексировано документов: {len(documents)}. Создано чанков: {total} (стратегия: `{strategy}`)."

    def compare_both_strategies(self, documents: dict[str, str]) -> dict:
        if not documents:
            return {"fixed_size": {"total_chunks": 0, "chunks": []}, "structural": {"total_chunks": 0, "chunks": []}}
        return self.indexer.compare_strategies(documents)

    def analyze_comparison(self, comparison_data: dict) -> str:
        """Генерирует аналитический отчет-сравнение двух стратегий чанкинга."""
        fixed_chunks = comparison_data["fixed_size"]["chunks"]
        struct_chunks = comparison_data["structural"]["chunks"]
        
        f_count = len(fixed_chunks)
        s_count = len(struct_chunks)
        
        # Считаем среднюю длину чанков в символах
        f_avg_len = sum(len(c["content"]) for c in fixed_chunks) / f_count if f_count > 0 else 0
        s_avg_len = sum(len(c["content"]) for c in struct_chunks) / s_count if s_count > 0 else 0
        
        # Формируем аналитический вывод
        report = f"""### 📊 Экспертный анализ стратегий чанкинга:

1. **Объемы и фрагментация:**
   - **Фиксированный размер:** создало **{f_count}** чанков (средняя длина: `{f_avg_len:.0f}` символов). Плюс — предсказуемый размер для векторной модели. Минус — возможен разрыв слов или предложений посередине.
   - **По структуре / абзацам:** создало **{s_count}** чанков (средняя длина: `{s_avg_len:.0f}` символов). Плюс — сохраняется естественная граница текста (абзацы, страницы). Минус — разброс по длине отрывков может быть значительным.

2. **Качество контекста и метаданных:**
   - Стратегия фиксированного размера использует техническую нумерацию символов.
   - Структурная стратегия автоматически извлекла смысловые заголовки (*«Тема: ...»*), что делает поиск и поиск по метаданным гораздо точнее для пользователя.

3. **Рекомендация для загруженного корпуса:**
   - Если текст разбит на логические абзацы или художественные сцены (как сказки или повести), **структурная стратегия** предпочтительнее, так как сохраняет целостность сюжета.
   - Если документ представляет собой сплошной массив технической документации без разметки, лучше использовать **фиксированный размер с перекрытием (overlap)**.
"""
        return report

    def get_index_stats(self) -> dict:
        return self.indexer.load_index()
