import streamlit as st
import os
from document_indexer import DocumentIndexer
from agent_day25 import IndexingAgentDay25

st.set_page_config(page_title="RAG Мини-Чат — День 25", page_icon="🤖", layout="wide")
agent = IndexingAgentDay25()
indexer = DocumentIndexer()

# Инициализация состояния сессии для чата и Task State
if "messages" not in st.session_state:
    st.session_state.messages = []

if "task_state" not in st.session_state:
    st.session_state.task_state = {
        "goal": "Обсуждение документов и поиск информации",
        "constraints": [],
        "terms": [],
        "progress": "Диалог начат"
    }

st.title("🔥 День 25: Мини-чат с RAG + Памятью задачи")

# Боковая панель: Память задачи (Task State) и настройки
with st.sidebar:
    st.header("🧠 Память задачи (Task State)")
    state = st.session_state.task_state
    st.markdown(f"**🎯 Цель:**\n{state.get('goal')}")
    st.markdown(f"**📌 Термины:**\n`{', '.join(state.get('terms', [])) if state.get('terms') else 'Нет'}`")
    st.markdown(f"**🚧 Ограничения:**\n{', '.join(state.get('constraints', [])) if state.get('constraints') else 'Нет'}")
    st.markdown(f"**📈 Прогресс:**\n{state.get('progress')}")
    
    if st.button("🧹 Очистить чат и память"):
        st.session_state.messages = []
        st.session_state.task_state = {
            "goal": "Обсуждение документов и поиск информации",
            "constraints": [],
            "terms": [],
            "progress": "Диалог очищен"
        }
        st.rerun()

    st.divider()
    st.header("⚙️ Настройки RAG")
    use_filter = st.checkbox("Включить порог релевантности", value=True)
    threshold = st.slider("Порог similarity", 0.0, 1.0, 0.1, 0.05)
    top_k_final = st.number_input("Top-K результатов", 1, 10, 3)

# Основная вкладка или загрузка файлов при необходимости
uploaded_files = st.file_uploader("📂 Загрузить документы для базы знаний (опционально)", accept_multiple_files=True, key="up_25")
if uploaded_files:
    docs = {}
    os.makedirs("data_cache", exist_ok=True)
    for f in uploaded_files:
        path = os.path.join("data_cache", f.name)
        with open(path, "wb") as out:
            out.write(f.getbuffer())
        docs[f.name] = f.getvalue().decode("utf-8", errors="ignore")
    if st.button("🚀 Проиндексировать загруженные файлы"):
        with st.spinner("Индексация..."):
            res = agent.indexer.build_and_save_index(docs, strategy="structural")
        st.success(f"Готово! Чанков создано: {res}")

st.divider()

# Отображение истории сообщений чата
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            st.markdown("---")
            st.markdown("**📚 Источники:**")
            for src in message["sources"]:
                st.markdown(f"- `{src}`")
        if "quotes" in message and message["quotes"]:
            with st.expander("📝 Посмотреть цитаты из чанков"):
                for q in message["quotes"]:
                    st.info(q)

# Ввод нового сообщения в чате
if prompt := st.chat_input("Задайте вопрос по документам..."):
    # Добавляем вопрос пользователя в историю
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Генерируем ответ ассистента с учетом истории и памяти задачи
    with st.chat_message("assistant"):
        with st.spinner("Думаю, ищу в базе знаний и обновляю контекст..."):
            response_data, updated_state = agent.generate_chat_response(
                query=prompt,
                history=st.session_state.messages[:-1],
                task_state=st.session_state.task_state,
                top_k_final=top_k_final,
                threshold=threshold,
                use_filter=use_filter
            )
            st.session_state.task_state = updated_state

        answer_text = response_data["answer"]
        sources = response_data["sources"]
        quotes = response_data["quotes"]

        st.markdown(answer_text)
        
        if sources:
            st.markdown("---")
            st.markdown("**📚 Источники:**")
            for src in sources:
                st.markdown(f"- `{src}`")
                
        if quotes:
            with st.expander("📝 Посмотреть цитаты из чанков"):
                for q in quotes:
                    st.info(q)

        # Сохраняем ответ ассистента в историю
        st.session_state.messages.append({
            "role": "assistant", 
            "content": answer_text,
            "sources": sources,
            "quotes": quotes
        })
    
    # Перезапуск для обновления панели Task State в сайдбаре
    st.rerun()
