from __future__ import annotations
import streamlit as st
from agent_day17 import GuardedFSMAgentWithMCPTools

st.set_page_config(
    page_title="День 17: Кастомный MCP-сервер и инструменты",
    page_icon="🛠️",
    layout="wide"
)

if "agent" not in st.session_state:
    st.session_state.agent = GuardedFSMAgentWithMCPTools()

agent: GuardedFSMAgentWithMCPTools = st.session_state.agent

# --- САЙДБАР ---
with st.sidebar:
    st.title("🛠️ День 17. MCP Tools")
    st.markdown("Интеграция собственного MCP-сервера и вызов инструментов.")
    st.divider()

    working_data = agent.load_memory("working")
    current_stage = working_data.get("stage", "planning")
    
    st.info(f"Текущий этап: **{current_stage.upper()}**")
    
    st.subheader("🎛️ Управление переходами")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➡️ В Execution"):
            success, msg = agent.change_stage("execution")
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
    with col2:
        if st.button("➡️ В Validation"):
            success, msg = agent.change_stage("validation")
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    if st.button("🏁 Завершить (Done)"):
        success, msg = agent.change_stage("done")
        if success:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    if st.button("↩️ Вернуть в Planning"):
        success, msg = agent.change_stage("planning")
        if success:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    st.divider()
    st.subheader("📦 Инструменты кастомного MCP")
    with st.spinner("Запрос инструментов..."):
        tools_result = agent.fetch_mcp_tools()
        
        if isinstance(tools_result, str):
            st.error(tools_result)
        elif tools_result:
            for t in tools_result:
                st.caption(f"🔧 **{t.name}**\n\n_{t.description}_")
        else:
            st.warning("Инструменты не обнаружены.")

    st.divider()
    if st.button("🔥 Сбросить всё"):
        agent.reset_all_memory()
        st.success("Сброшено к началу!")
        st.rerun()

# --- ОСНОВНОЙ ЭКРАН (ЧАТ) ---
st.title("🛠️ День 17. Агент с вызовом MCP-инструментов")
st.markdown("Агент подключается к собственному MCP-серверу (`mcp_server_day17.py`), запрашивает инструменты и умеет вызывать их по вашему запросу.")
st.divider()

st_messages = agent.load_memory("short_term")
for msg in st_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Напишите запрос агенту (например: 'Проверь статус фичи payment')...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Агент выполняет запрос и опрашивает MCP..."):
            try:
                res = agent.send_message(user_input)
                st.markdown(res["reply"])
            except Exception as e:
                st.error(str(e))
