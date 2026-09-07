import streamlit as st
from agent import LLMAgent

st.set_page_config(page_title="Day 6: AI Agent", page_icon="🤖")

st.title("🤖 AI Challenge - День 6: Первый агент")
st.write("Веб-интерфейс для агента, инкапсулирующего логику работы с LLM и стек сообщений (память).")

# Инициализируем агента в памяти сессии Streamlit, чтобы он не сбрасывался при каждом клике
if "agent" not in st.session_state:
    st.session_state.agent = LLMAgent(model_name="glm-4.7-flash")

# Инициализируем историю сообщений для отрисовки в UI
if "messages" not in st.session_state:
    st.session_state.messages = []

# Отрисовываем историю чата на экране
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Поле ввода текста внизу страницы
if user_input := st.chat_input("Напишите сообщение агенту..."):
    # Показываем сообщение пользователя в интерфейсе
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Получаем ответ от нашего агента (он сам внутри держит стек и отправляет в LLM)
    with st.chat_message("assistant"):
        with st.spinner("Агент думает..."):
            try:
                response_text = st.session_state.agent.chat(user_input)
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
            except Exception as e:
                error_msg = f"Ошибка: {e}"
                st.error(error_msg)
