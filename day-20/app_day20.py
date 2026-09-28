import streamlit as st
from agent_day20 import OrchestrationAgentDay20

st.set_page_config(page_title="День 20. Мультисерверная оркестрация MCP", page_icon="🌐", layout="centered")

st.title("🌐 День 20. Orchestration MCP (Мультисерверная оркестрация)")
st.markdown("Агент координирует работу независимых MCP-серверов (`AnalyticsServer` и `CRMServer`) и ведет фоновые отчеты 24/7.")

if "agent" not in st.session_state:
    st.session_state.agent = OrchestrationAgentDay20(background_interval=60)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Боковая панель со статусом фонового планировщика
with st.sidebar:
    st.subheader("⏰ Фоновый режим (24/7)")
    if st.button("🔄 Проверить фоновый отчет"):
        st.rerun()
    st.info(st.session_state.agent.latest_bg_report)
    
    if st.button("🗑️ Очистить историю"):
        st.session_state.messages = []
        st.session_state.agent.reset_all_memory()
        st.rerun()

# Отображение истории чата
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Ввод пользователя
user_prompt = st.chat_input("Например: Запусти полный флоу по платежам")

if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Выполняется кросс-серверная оркестрация..."):
            try:
                res = st.session_state.agent.send_message(user_prompt)
                reply = res["reply"]
            except Exception as e:
                reply = f"❌ Ошибка: {e}"
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
