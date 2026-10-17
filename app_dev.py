import streamlit as st
from agent_dev import DevAssistantAgent

st.set_page_config(page_title="Day 31: Dev Assistant", page_icon="🧑‍💻", layout="wide")

st.title("🧑‍💻 AI Challenge - День 31: Ассистент разработчика")
st.write("Локальный AI-ассистент с RAG по документации проекта и MCP-подключением к GitHub-репозиторию.")

if "dev_agent" not in st.session_state:
    st.session_state.dev_agent = DevAssistantAgent()

agent = st.session_state.dev_agent

with st.sidebar:
    st.header("⚙️ Окружение проекта")
    st.write("Репозиторий: `NikaMalinovskaia/AI_challenge`")
    st.divider()
    st.subheader("💡 Команды")
    st.code("/help — Справка по проекту", language="text")
    
    if st.button("🧹 Очистить чат"):
        agent.reset_memory()
        st.rerun()

for msg in agent.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("Введите запрос или /help..."):
    with st.chat_message("user"):
        st.markdown(user_input)
        
    with st.chat_message("assistant"):
        with st.spinner("Сканирование репозитория на GitHub и генерация ответа..."):
            try:
                ans, dur = agent.chat(user_input)
                st.markdown(ans)
                
                with st.expander("🛠 Метрики сессии"):
                    st.write(f"⏱ **Время ответа:** {dur:.2f} сек.")
                    st.write(f"🌐 **Источник:** GitHub API (`NikaMalinovskaia/AI_challenge`)")
            except Exception as e:
                st.error(f"Ошибка: {e}")