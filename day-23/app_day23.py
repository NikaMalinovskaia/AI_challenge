import streamlit as st
import os
from document_indexer import DocumentIndexer
from agent_day23 import IndexingAgentDay23

st.set_page_config(page_title="RAG Агент — День 23", page_icon="🤖", layout="wide")
agent = IndexingAgentDay23()
indexer = DocumentIndexer()

st.title("🔥 День 23: Реранкинг, Фильтрация и Query Rewrite")

def get_docs_from_upload(uploaded_files):
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

# Боковая панель: Настройки фильтрации и контрольные вопросы
with st.sidebar:
    st.header("⚙️ Настройки фильтрации (День 23)")
    use_filter = st.checkbox("Включить порог релевантности", value=True)
    threshold = st.slider("Порог similarity (threshold)", min_value=0.0, max_value=1.0, value=0.1, step=0.05)
    
    top_k_initial = st.number_input("Top-K до фильтрации", min_value=1, max_value=20, value=5)
    top_k_final = st.number_input("Top-K после фильтрации", min_value=1, max_value=10, value=3)
    
    use_rewrite = st.checkbox("Включить Query Rewrite", value=True)

    st.divider()
    st.header("📋 10 контрольных вопросов")
    benchmarks = agent.get_test_benchmarks()
    
    if not benchmarks:
        st.info("Загрузите файлы и сгенерируйте бенчмарки на вкладке 1.")
    else:
        for b in benchmarks:
            with st.expander(f"№{b.get('id', '?')}: {b.get('question', '')[:22]}..."):
                st.markdown(f"**❓ Вопрос:**\n{b.get('question')}")
                st.markdown(f"**🎯 Ожидание:**\n{b.get('expectation')}")
                sources_list = b.get('expected_sources', [])
                st.markdown(f"**📂 Источники:**\n`{', '.join(sources_list) if sources_list else 'Нет'}`")

tab1, tab2 = st.tabs(["📂 1. Индексация и Бенчмарки", "💬 2. Улучшенный RAG и Сравнение"])

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
                with st.spinner("Генерация вопросов с ожиданиями и источниками..."):
                    docs = get_docs_from_upload(uploaded_files)
                    benchs = agent.generate_dynamic_benchmarks(docs)
                st.success(f"Успешно создано бенчмарков: {len(benchs)}!")
                st.rerun()
            else:
                st.warning("Сначала загрузите файлы.")

with tab2:
    st.subheader("Тестирование RAG с фильтрацией и реранкингом")
    query = st.text_input("Введите вопрос по вашим документам:")
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        run_no_rag = st.button("🤖 Запрос БЕЗ RAG")
    with col_b:
        run_with_rag = st.button("🔍 Запрос С RAG (фильтр ВКЛ)")
    with col_c:
        run_compare = st.button("⚖️ Сравнить: Без фильтра/rewriting vs С фильтром")
        
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
            with st.spinner("Поиск, реранкинг и генерация ответа..."):
                result = agent.generate_answer_with_rag(
                    query, 
                    top_k_initial=top_k_initial, 
                    top_k_final=top_k_final, 
                    threshold=threshold, 
                    use_filter=use_filter, 
                    use_rewrite=use_rewrite
                )
            
            if use_rewrite and result.get("rewritten_query") != query:
                st.info(f"🔄 Переформулированный запрос (Query Rewrite): *{result.get('rewritten_query')}*")

            st.markdown("### Ответ модели (С фильтрацией и реранкингом):")
            st.success(result["answer"])
            
            st.markdown(f"📊 *Отсечено нерелевантных чанков:* `{result.get('filtered_out_count', 0)}`")
            
            st.markdown("### 📚 Использованные источники:")
            if result["sources"]:
                for src in result["sources"]:
                    st.markdown(f"- `{src}`")
            else:
                st.markdown("- Источники не найдены.")
                
            with st.expander("🛠️ Посмотреть отфильтрованные чанки (контекст):", expanded=False):
                for idx, chunk in enumerate(result.get("retrieved_chunks", [])):
                    score_val = chunk.get('score', 'N/A')
                    st.markdown(f"**Чанк #{idx+1} | Score:** `{score_val}` | **Источник:** `{chunk.get('source')}`")
                    st.code(chunk.get("content"), language="text")

    if run_compare:
        if not query:
            st.warning("Выполнение сравнительного анализа...")
        else:
            with st.spinner("Сравнение режимов (Без фильтра vs С фильтром)..."):
                # Режим 1: Качество БЕЗ фильтра и БЕЗ rewriting
                res_no_filter = agent.generate_answer_with_rag(
                    query, 
                    top_k_initial=top_k_final, 
                    top_k_final=top_k_final, 
                    threshold=0.0, 
                    use_filter=False, 
                    use_rewrite=False
                )
                # Режим 2: Качество С фильтром, реранкингом и rewriting
                res_with_filter = agent.generate_answer_with_rag(
                    query, 
                    top_k_initial=top_k_initial, 
                    top_k_final=top_k_final, 
                    threshold=threshold, 
                    use_filter=use_filter, 
                    use_rewrite=use_rewrite
                )
            
            st.markdown("---")
            st.subheader("📊 Сравнение качества по заданию Дня 23")
            comp_col1, comp_col2 = st.columns(2)
            
            with comp_col1:
                st.markdown("### 🔴 Качество без фильтра / rewriting")
                st.write(res_no_filter["answer"])
                st.markdown("**Источники:**")
                for s in res_no_filter["sources"]:
                    st.markdown(f"- `{s}`")
                
            with comp_col2:
                st.markdown("### 🟢 Качество с фильтром и rewriting")
                st.success(res_with_filter["answer"])
                st.markdown(f"*Отсечено мусора:* `{res_with_filter.get('filtered_out_count', 0)}`")
                st.markdown("**Источники:**")
                for s in res_with_filter["sources"]:
                    st.markdown(f"- `{s}`")
