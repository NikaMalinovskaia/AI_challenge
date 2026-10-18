import streamlit as st
from agent_dev import DevAssistantAgent

st.set_page_config(page_title="Day 31: Pro Dev Assistant", page_icon="🧑‍💻", layout="wide")

st.title("🧑‍💻 AI Challenge - День 31: Профессиональный Ассистент (Tool Calling)")
st.write("Ассистент с поддержкой автономного вызова инструментов (Tool Calling) для работы с GitHub и Git.")

if "dev_agent" not in st.session_state:
    st.session_state.dev_agent = DevAssistantAgent()

agent = st.session_state.dev_agent

with st.sidebar:
    st.header("⚙️ Архитектура")
    st.write("Репозиторий: `NikaMalinovskaia/AI_challenge`")
    st.write("Режим: **Native Tool Calling**")
    st.divider()
    
    if st.button("🧹 Очистить чат"):
        agent.reset_memory()
        st.rerun()

# Отображение истории
for msg in agent.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("Спросите про проект, ветки или код (например: 'Покажи файлы в day-30')..."):
    with st.chat_message("user"):
        st.markdown(user_input)
        
    with st.chat_message("assistant"):
        with st.spinner("Агент думает и вызывает инструменты..."):
            try:
                ans, dur = agent.chat(user_input)
                st.markdown(ans)
                
                with st.expander("🛠 Метрики сессии"):
                    st.write(f"⏱ **Время ответа:** {dur:.2f} сек.")
                    st.write(f"⚙️ **Метод:** Автономный вызов инструментов (Tool Calling)")
            except Exception as e:
                st.error(f"Ошибка: {e}")
