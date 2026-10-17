import streamlit as st
from agent_day21 import IndexingAgentDay21

st.set_page_config(page_title="День 21. Индексация документов и Чанкинг", page_icon="📚", layout="wide")

if "agent" not in st.session_state:
    st.session_state.agent = IndexingAgentDay21()

agent = st.session_state.agent

st.title("📚 День 21. Индексация документов и сравнение стратегий Chunking")
st.markdown("Загружайте PDF-файлы или тексты, настраивайте пайплайн и управляйте умными заголовками чанков.")

# --- Боковая панель для загрузки файлов ---
st.sidebar.header("📁 Загрузка документов")
uploaded_files = st.sidebar.file_uploader(
    "Загрузите PDF, текстовые файлы или код",
    type=["txt", "md", "py", "pdf"],
    accept_multiple_files=True
)

corpus = {}
if uploaded_files:
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Статус загруженных файлов:")
    for file in uploaded_files:
        if file.name.endswith(".pdf"):
            text_content = agent.indexer.extract_text_from_pdf(file.read())
        else:
            text_content = file.read().decode("utf-8", errors="ignore")
        
        corpus[file.name] = text_content
        
        file_size_kb = len(file.getvalue()) / 1024
        char_count = len(text_content)
        st.sidebar.success(f"✅ **{file.name}**\n\n"
                           f"• Размер: `{file_size_kb:.1f} KB`\n"
                           f"• Символов: `{char_count}`\n"
                           f"• Статус: **Готов к индексации**")
else:
    corpus = {
        "README_default.md": (
            "### Введение в проект\n"
            "Данный проект представляет собой модульную систему автономных ИИ-агентов.\n"
            "Система поддерживает многошаговую оркестрацию через Model Context Protocol (MCP)."
        )
    }
    st.sidebar.info("💡 Загрузите файлы через поле выше. Сейчас используется демо-документ.")

tab1, tab2 = st.tabs(["🚀 Индексация по одной стратегии", "⚖️ Сравнение стратегий (Fixed vs Structural)"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("⚙️ Управление индексацией")
        strategy_choice = st.selectbox(
            "Выберите стратегию чанкинга:",
            options=["fixed_size", "structural"],
            format_func=lambda x: "Фиксированный размер (Fixed Size)" if x == "fixed_size" else "По структуре и умным заголовкам (Structural)"
        )
        if st.button("🚀 Запустить индексацию корпуса"):
            res = agent.run_indexing(corpus, strategy=strategy_choice)
            st.success(res)
            st.rerun()
            
    with col2:
        st.subheader("📊 Текущий статус индекса")
        index_data = agent.get_index_stats()
        st.metric("Стратегия в файле", index_data.get("strategy", "Не запущен"))
        st.metric("Всего чанков", index_data.get("total_chunks", 0))

    st.divider()
    st.subheader("🔍 Просмотр чанков и метаданных в сохраненном индексе")
    chunks = index_data.get("chunks", [])
    if chunks:
        for chunk in chunks:
            with st.expander(f"[{chunk['chunk_id']}] Источник: {chunk['source']} | 🏷️ {chunk['section']}"):
                st.markdown(f"**Текст отрывка:**\n> {chunk['content']}")
                st.json({
                    "chunk_id": chunk["chunk_id"],
                    "source": chunk["source"],
                    "smart_section_title": chunk["section"],
                    "strategy": chunk["strategy"]
                })
    else:
        st.info("Индекс пуст. Нажмите кнопку «Запустить индексацию корпуса» выше.")

with tab2:
    st.subheader("⚖️ Сравнение двух стратегий на загруженном корпусе")
    st.markdown("Система выполнит параллельное разбиение загруженных документов обоими методами и проведет автоматический сравнительный анализ.")
    
    if st.button("🔍 Сравнить обе стратегии и выдать анализ"):
        comparison = agent.compare_both_strategies(corpus)
        
        # Выдаем экспертный анализ результата
        analysis_report = agent.analyze_comparison(comparison)
        st.info(analysis_report)
        
        st.divider()
        
        col_f, col_s = st.columns(2)
        
        with col_f:
            st.markdown("### 📏 Фиксированный размер")
            f_data = comparison["fixed_size"]
            st.metric("Кол-во чанков", f_data["total_chunks"])
            for chunk in f_data["chunks"]:
                with st.expander(f"[{chunk['chunk_id']}] {chunk['section']}"):
                    st.text(chunk["content"])
                    
        with col_s:
            st.markdown("### 🏛️ По структуре и умным заголовкам")
            s_data = comparison["structural"]
            st.metric("Кол-во чанков", s_data["total_chunks"])
            for chunk in s_data["chunks"]:
                with st.expander(f"[{chunk['chunk_id']}] {chunk['section']}"):
                    st.text(chunk["content"])
