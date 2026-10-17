import streamlit as st
import os
from document_indexer import DocumentIndexer
from agent_day22 import IndexingAgentDay22

st.set_page_config(page_title="RAG Агент — День 22", page_icon="🤖", layout="wide")
agent = IndexingAgentDay22()
indexer = DocumentIndexer()

st.title("🤖 День 22: Первый RAG-запрос и Контрольные Бенчмарки")

def get_docs_from_upload(uploaded_files):
    """Универсальная функция: сохраняет файлы в кэш и извлекает из них текст."""
    docs = {}
    os.makedirs("data_cache", exist_ok=True)
    for f in uploaded_files:
        path = os.path.join("data_cache", f.name)
        with open(path, "wb") as out:
            out.write(f.getbuffer())
        
        try:
            if f.name.endswith('.pdf'):
                text = indexer.extract_text_from_pdf(f.getbuffer())
            else:
                text = f.getvalue().decode("utf-8", errors="ignore")
            docs[f.name] = text
        except Exception as e:
            st.error(f"Ошибка при чтении файла {f.name}: {e}")
    return docs

# Боковая панель: 10 контрольных вопросов с ожиданиями и источниками
with st.sidebar:
    st.header("📋 10 контрольных вопросов")
    benchmarks = agent.get_test_benchmarks()
    
    if not benchmarks:
        st.info("Загрузите файлы и нажмите «Сгенерировать 10 вопросов» на вкладке 1.")
    else:
        for b in benchmarks:
            with st.expander(f"№{b.get('id', '?')}: {b.get('question', '')[:25]}..."):
                st.markdown(f"**❓ Вопрос:**\n{b.get('question')}")
                st.markdown(f"**🎯 Ожидание:**\n{b.get('expectation')}")
                sources_list = b.get('expected_sources', [])
                st.markdown(f"**📂 Источники:**\n`{', '.join(sources_list) if sources_list else 'Нет'}`")

tab1, tab2 = st.tabs(["📂 1. Индексация и Бенчмарки", "💬 2. Сравнение (С RAG / Без RAG)"])

with tab1:
    st.subheader("Загрузка базы знаний и генерация бенчмарков")
    uploaded_files = st.file_uploader("Загрузите документы (txt, pdf, md)", accept_multiple_files=True, key="uploader_files")
    strategy = st.selectbox("Стратегия чанкинга", ["structural", "fixed_size"])
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Запустить индексацию"):
            if uploaded_files:
                with st.spinner("Индексация документов..."):
                    docs = get_docs_from_upload(uploaded_files)
                    res = agent.run_indexing(docs, strategy)
                st.success(res)
            else:
                st.warning("Сначала загрузите файлы.")
                
    with col2:
        if st.button("🎯 Сгенерировать 10 контрольных вопросов"):
            if uploaded_files:
                with st.spinner("Генерация вопросов с ожиданиями и источниками через LLM..."):
                    docs = get_docs_from_upload(uploaded_files)
                    benchs = agent.generate_dynamic_benchmarks(docs)
                st.success(f"Успешно создано бенчмарков: {len(benchs)}!")
                st.rerun()
            else:
                st.warning("Сначала загрузите файлы.")

with tab2:
    st.subheader("Тестирование RAG-пайплайна и Сравнение")
    query = st.text_input("Введите вопрос по вашим документам:")
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        run_no_rag = st.button("🤖 Запрос БЕЗ RAG")
    with col_b:
        run_with_rag = st.button("🔍 Запрос С RAG")
    with col_c:
        run_compare = st.button("⚖️ Сравнить оба режима")
        
    if run_no_rag:
        if not query:
            st.warning("Введите вопрос.")
        else:
            with st.spinner("Запрос к модели без контекста..."):
                ans = agent.generate_answer_without_rag(query)
            st.markdown("### Ответ модели (Без RAG):")
            st.write(ans)
            
    if run_with_rag:
        if not query:
            st.warning("Введите вопрос.")
        else:
            with st.spinner("Поиск чанков и формирование RAG-ответа..."):
                result = agent.generate_answer_with_rag(query)
            st.markdown("### Ответ модели (С RAG):")
            st.success(result["answer"])
            
            st.markdown("### 📚 Использованные источники:")
            if result["sources"]:
                for src in result["sources"]:
                    st.markdown(f"- `{src}`")
            else:
                st.markdown("- Источники не найдены.")
                
            with st.expander("🛠️ Посмотреть найденные чанки (контекст):", expanded=False):
                for idx, chunk in enumerate(result.get("retrieved_chunks", [])):
                    st.markdown(f"**Чанк #{idx+1} | Источник:** `{chunk.get('source')}` | **Раздел:** `{chunk.get('section')}`")
                    st.code(chunk.get("content"), language="text")

    if run_compare:
        if not query:
            st.warning("Введите вопрос.")
        else:
            with st.spinner("Выполнение параллельного сравнения (Без RAG vs С RAG)..."):
                ans_no_rag = agent.generate_answer_without_rag(query)
                result_rag = agent.generate_answer_with_rag(query)
            
            st.markdown("---")
            st.subheader("📊 Результаты параллельного сравнения")
            comp_col1, comp_col2 = st.columns(2)
            
            with comp_col1:
                st.markdown("### 🔴 Ответ без RAG")
                st.write(ans_no_rag)
                
            with comp_col2:
                st.markdown("### 🟢 Ответ с RAG")
                st.success(result_rag["answer"])
                
                st.markdown("**📚 Источники:**")
                if result_rag["sources"]:
                    for src in result_rag["sources"]:
                        st.markdown(f"- `{src}`")
                else:
                    st.markdown("- Источники не найдены.")
