from __future__ import annotations
import streamlit as st
from agent_day18 import GuardedFSMAgentWithScheduler

st.set_page_config(
    page_title="День 18: Планировщик и фоновые задачи MCP",
    page_icon="⏱️",
    layout="wide"
)

if "agent" not in st.session_state:
    st.session_state.agent = GuardedFSMAgentWithScheduler()

agent: GuardedFSMAgentWithScheduler = st.session_state.agent

with st.sidebar:
    st.title("⏱️ День 18. Scheduler")
    st.markdown("Фоновый сбор данных и регулярный summary через MCP.")
    st.divider()

    working_data = agent.load_memory("working")
    current_stage = working_data.get("stage", "planning")
    
    st.info(f"Текущий этап: **{current_stage.upper()}**")
    
    st.subheader("🎛️ Управление переходами")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➡️ В Execution"):
            success, msg = agent.change_stage("execution")
            if success: st.rerun()
            else: st.error(msg)
    with col2:
        if st.button("➡️ В Validation"):
            success, msg = agent.change_stage("validation")
            if success: st.rerun()
            else: st.error(msg)

    if st.button("🏁 Завершить (Done)"):
        success, msg = agent.change_stage("done")
        if success: st.rerun()
        else: st.error(msg)

    if st.button("↩️ Вернуть в Planning"):
        success, msg = agent.change_stage("planning")
        if success: st.rerun()
        else: st.error(msg)

    st.divider()
    st.subheader("📦 Инструменты планировщика")
    tools_result = agent.fetch_mcp_tools()
    if isinstance(tools_result, str):
        st.error(tools_result)
    elif tools_result:
        for t in tools_result:
            st.caption(f"⏱️ **{t.name}**\n\n_{t.description}_")

    st.divider()
    if st.button("🔥 Сбросить всё"):
        agent.reset_all_memory()
        st.success("Сброшено!")
        st.rerun()

st.title("⏱️ День 18. Агент с фоновым сбором метрик")
st.markdown("Агент сохраняет данные в JSON и умеет выдавать регулярную сводку (`summary`) по запросу.")
st.divider()

st_messages = agent.load_memory("short_term")
for msg in st_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Напишите запрос (например: 'Собери метрики' или 'Покажи сводку')...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Агент обрабатывает фоновую задачу..."):
            try:
                res = agent.send_message(user_input)
                st.markdown(res["reply"])
            except Exception as e:
                st.error(str(e))
