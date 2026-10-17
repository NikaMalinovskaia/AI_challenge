import streamlit as st
from agent_rag import LocalRAGAgent

st.set_page_config(page_title="Day 29: Local LLM Optimization", page_icon="⚡", layout="wide")

st.title("⚡ AI Challenge - День 29: Оптимизация локальной LLM")
st.write("Тюнинг гиперпараметров (Temperature, Max Tokens, Context Window) и кастомизация промпт-шаблонов.")

if "rag_agent" not in st.session_state:
    st.session_state.rag_agent = LocalRAGAgent()

agent = st.session_state.rag_agent

# Панель управления оптимизацией в сайдбаре
with st.sidebar:
    st.header("🎛️ Гиперпараметры")
    temperature = st.slider("Temperature (креативность)", 0.0, 1.0, 0.2, 0.1)
    max_tokens = st.slider("Max Tokens (лимит длины)", 100, 1000, 400, 50)
    
    st.header("📝 Шаблон промпта")
    prompt_template = st.selectbox(
        "Выберите роль/шаблон", 
        ["Стандартный", "Строгий код-ревьюер", "Преподаватель-наставник"]
    )
    
    agent.temperature = temperature
    agent.max_tokens = max_tokens
    
    st.divider()
    if st.button("🔄 Очистить историю"):
        agent.reset_memory()
        st.rerun()

tab_chat, tab_compare = st.tabs(["💬 Чат с оптимизированной моделью", "📊 Сравнение: До и После оптимизации"])

with tab_chat:
    for msg in agent.history:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant"):
                st.markdown(msg["content"])
                
    if user_input := st.chat_input("Задайте вопрос или вставьте код на C#..."):
        with st.chat_message("user"):
            st.markdown(user_input)
            
        with st.chat_message("assistant"):
            with st.spinner("Генерация с учетом оптимизации..."):
                try:
                    ans, sources, dur = agent.chat_single(user_input, prompt_template)
                    st.markdown(ans)
                    with st.expander("⚙️ Метрики оптимизации"):
                        st.write(f"⏱ **Время ответа:** {dur:.2f} сек.")
                        st.write(f"🌡 **Temperature:** {temperature} | 📏 **Max Tokens:** {max_tokens}")
                except Exception as e:
                    st.error(f"Ошибка: {e}")

with tab_compare:
    st.header("📊 Бенчмарк оптимизации")
    st.write("Сравнение поведения модели при разных настройках (например, высокая температура vs низкая, стандартный промпт vs код-ревьюер).")
    
    test_q = st.text_input("Тестовый запрос", "Зачем в C# нужны свойства вместо публичных полей?")
    
    if st.button("🚀 Запустить бенчмарк"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("⚙️ До оптимизации (Temp=0.8, Стандарт)")
            ans1, _, d1 = agent.chat_single(test_q, "Стандартный", custom_temp=0.8, custom_max_tokens=800)
            st.markdown(ans1)
            st.caption(f"Время: {d1:.2f} сек.")
            
        with col2:
            st.subheader("⚡ После оптимизации (Temp=0.1, Код-ревьюер)")
            ans2, _, d2 = agent.chat_single(test_q, "Строгий код-ревьюер", custom_temp=0.1, custom_max_tokens=300)
            st.markdown(ans2)
            st.caption(f"Время: {d2:.2f} сек.")
