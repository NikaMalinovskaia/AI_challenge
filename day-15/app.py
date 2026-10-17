from __future__ import annotations
import json
import streamlit as st
from agent_day15 import GuardedFSMAgent

st.set_page_config(
    page_title="День 15: Контролируемые переходы состояний",
    page_icon="🚦",
    layout="wide"
)

if "agent" not in st.session_state:
    st.session_state.agent = GuardedFSMAgent()

agent: GuardedFSMAgent = st.session_state.agent

# --- САЙДБАР ---
with st.sidebar:
    st.title("🚦 День 15. FSM Guard")
    st.markdown("Контроль переходов: **Planning ➔ Execution ➔ Validation ➔ Done**.")
    st.divider()

    working_data = agent.load_memory("working")
    current_stage = working_data.get("stage", "planning")
    
    st.info(f"Текущий этап: **{current_stage.upper()}**")
    
    st.subheader("🎛️ Управление переходами")
    
    # Кнопки для валидируемых переходов
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
    if st.button("🔥 Сбросить всё"):
        agent.reset_all_memory()
        st.success("Сброшено к началу!")
        st.rerun()

# --- ОСНОВНОЙ ЭКРАН (ЧАТ) ---
st.title("🚦 День 15. Контролируемый жизненный цикл задачи")
st.markdown("Попробуйте попросить агента сделать финал или валидацию, находясь на этапе `planning` — FSM заблокирует переход.")
st.divider()

st_messages = agent.load_memory("short_term")
for msg in st_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Напишите запрос агенту...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Агент проверяет правила переходов..."):
            try:
                res = agent.send_message(user_input)
                st.markdown(res["reply"])
            except Exception as e:
                st.error(str(e))
