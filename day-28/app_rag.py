import streamlit as st
from agent_rag import LocalRAGAgent

st.set_page_config(page_title="Day 28: Local RAG vs Cloud", page_icon="🧠", layout="wide")

st.title("🧠 AI Challenge - День 28: Локальный RAG + Сравнение с облаком")

# Инициализация агента в сессии (сохраняется при переключениях)
if "rag_agent" not in st.session_state:
    st.session_state.rag_agent = LocalRAGAgent()

agent = st.session_state.rag_agent

# Боковая панель
with st.sidebar:
    st.header("⚙️ Управление")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.3, 0.1)
    agent.temperature = temperature
    
    st.divider()
    if st.button("🔄 Очистить всю память"):
        agent.reset_memory()
        st.rerun()

# Создаем вкладки для основного чата и отдельного блока сравнения
tab_chat, tab_compare = st.tabs(["💬 Чат / Сессия (с сохранением истории)", "📊 Блок сравнения (Локальная vs Облачная)"])

with tab_chat:
    st.write("Здесь вы можете общаться с агентом. При переключении режимов история каждого чата **сохраняется** благодаря раздельной памяти.")
    
    # Выбор режима для чата
    chat_mode = st.radio("Активный режим чата", ["Локальный (Ollama / qwen2.5)", "Облачный (glm-4.7-flash)"], horizontal=True)
    mode_key = "local" if "Локальный" in chat_mode else "cloud"
    
    # Отрисовка истории текущего режима
    for msg in agent.histories[mode_key][1:]:
        if msg["role"] == "user":
            display_text = msg["content"].split("Вопрос пользователя: ")[-1].split("\n\n")[0]
            with st.chat_message("user"):
                st.markdown(display_text)
        else:
            with st.chat_message("assistant"):
                st.markdown(msg["content"])
                
    # Ввод сообщения
    if user_input := st.chat_input("Введите вопрос по C# ООП..."):
        with st.chat_message("user"):
            st.markdown(user_input)
            
        with st.chat_message("assistant"):
            with st.spinner("Генерация ответа..."):
                try:
                    ans, sources, dur = agent.chat_single(user_input, mode_key)
                    st.markdown(ans)
                    with st.expander("🔍 Источники (Retrieval) и метрики"):
                        st.write(f"⏱ Время: {dur:.2f} сек.")
                        for src in sources:
                            st.caption(f"[{src['id']}] {src['topic']}")
                except Exception as e:
                    st.error(f"Ошибка: {e}")

with tab_compare:
    st.header("📊 Сравнение ответов, качества и скорости")
    st.write("Введите тестовый запрос, чтобы одновременно отправить его на локальную модель (`qwen2.5`) и в облако через единый локальный Retrieval-индекс.")
    
    compare_query = st.text_input("Запрос для сравнения", "Зачем в C# нужны свойства вместо публичных полей?")
    
    if st.button("🚀 Запустить сравнение"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💻 Локальная (Ollama / qwen2.5)")
            with st.spinner("Локальный расчет..."):
                try:
                    ans_loc, src_loc, dur_loc = agent.chat_single(compare_query, "local")
                    st.markdown(ans_loc)
                    st.success(f"⏱ Скорость: {dur_loc:.2f} сек.")
                    st.info("🔒 Стабильность: 100% локально (без интернета)")
                except Exception as e:
                    st.error(f"Ошибка локальной модели: {e}")
                    
        with col2:
            st.subheader("☁️ Облачная (glm-4.7-flash)")
            with st.spinner("Облачный запрос..."):
                try:
                    ans_cld, src_cld, dur_cld = agent.chat_single(compare_query, "cloud")
                    st.markdown(ans_cld)
                    st.warning(f"⏱ Скорость: {dur_cld:.2f} сек.")
                    st.info("🌐 Стабильность: зависит от сети")
                except Exception as e:
                    st.error(f"Ошибка облачной модели: {e}")
