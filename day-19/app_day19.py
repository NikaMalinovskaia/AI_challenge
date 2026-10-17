import streamlit as st
from agent_day19 import PipelineAgentDay19

st.set_page_config(page_title="День 19. Композиция MCP-инструментов", page_icon="🔗", layout="centered")

st.title("🔗 День 19. Композиция MCP-инструментов (Пайплайн)")
st.markdown("Агент автоматически связывает инструменты в цепочку: **Search ➔ Summarize ➔ SaveToFile**.")

if "agent" not in st.session_state:
    st.session_state.agent = PipelineAgentDay19()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Кнопка сброса
if st.sidebar.button("🗑️ Очистить историю"):
    st.session_state.messages = []
    st.session_state.agent.reset_all_memory()
    st.rerun()

# Отображение истории чата
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Ввод пользователя
user_prompt = st.chat_input("Например: Запусти пайплайн по теме MCP")

if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Выполняется цепочка MCP-инструментов..."):
            try:
                res = st.session_state.agent.send_message(user_prompt)
                reply = res["reply"]
            except Exception as e:
                reply = f"❌ Ошибка: {e}"
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
