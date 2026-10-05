import streamlit as st
import os
from document_indexer import DocumentIndexer
from agent_day24 import IndexingAgentDay24

st.set_page_config(page_title="RAG Агент — День 24", page_icon="🤖", layout="wide")
agent = IndexingAgentDay24()
indexer = DocumentIndexer()

st.title("🔥 День 24: Цитаты, Источники и Анти-галлюцинации")

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

# Боковая панель с настройками порога и бенчмарками
with st.sidebar:
    st.header("⚙️ Настройки анти-галлюцинаций")
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

tab1, tab2 = st.tabs(["📂 1. Индексация и Бенчмарки", "💬 2. Защищенный RAG и Проверка"])

with tab1:
    st.subheader("Загрузка базы знаний и генерация бенчмарков")
    uploaded_files = st.file_uploader("Загрузите документы (txt, pdf, md)", accept_multiple_files=True, key="uploader_files_24")
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
    st.subheader("Тестирование RAG с обязательными цитатами и режимом «Не знаю»")
    query = st.text_input("Введите вопрос по вашим документам (или проверьте на несуществующий факт):")
    
    run_query = st.button("🔍 Запросить с анти-галлюцинационной защитой")
        
    if run_query:
        if not query:
            st.warning("Введите вопрос.")
        else:
            with st.spinner("Анализ запроса, поиск и проверка релевантности..."):
                result = agent.generate_answer_with_rag(
                    query, 
                    top_k_initial=top_k_initial, 
                    top_k_final=top_k_final, 
                    threshold=threshold, 
                    use_filter=use_filter, 
                    use_rewrite=use_rewrite
                )
            
            if use_rewrite and result.get("rewritten_query") != query:
                st.info(f"🔄 Переформулированный запрос: *{result.get('rewritten_query')}*")

            if result.get("is_i_dont_know"):
                st.warning(f"🛡️ Сработал режим защиты от галлюцинаций: {result['answer']}")
            else:
                st.markdown("### 💬 Ответ модели:")
                st.success(result["answer"])
                
                st.markdown("### 📚 Обязательные источники:")
                for src in result["sources"]:
                    st.markdown(f"- `{src}`")
                    
                st.markdown("### 📝 Полные цитаты из чанков:")
                for q in result["quotes"]:
                    st.info(q)
                
                st.markdown(f"📊 *Отсечено нерелевантных чанков фильтром:* `{result.get('filtered_out_count', 0)}`")
