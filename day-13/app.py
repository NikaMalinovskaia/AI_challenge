from __future__ import annotations
import json
import streamlit as st
from agent_day13 import FSMTaskAgent

# Настройка страницы Streamlit
st.set_page_config(
    page_title="День 13: Управление задачей через FSM",
    page_icon="🔥",
    layout="wide"
)

# Инициализация агента в сессии Streamlit
if "agent" not in st.session_state:
    st.session_state.agent = FSMTaskAgent()

agent: FSMTaskAgent = st.session_state.agent

# --- САЙДБАР: ОПЕРАЦИИ С ПАМЬЯТЬЮ И FSM ---
with st.sidebar:
    st.title("🔥 День 13. Состояние задачи (FSM)")
    st.markdown("Агент управляет задачей через конечный автомат: **Planning ➔ Execution ➔ Validation ➔ Done**.")
    st.divider()

    # Загружаем текущие данные для отображения
    working_data = agent.load_memory("working")
    short_term_data = agent.load_memory("short_term")
    long_term_data = agent.load_memory("long_term")

    st.subheader("⚙️ FSM State (Working)")
    
    # Ручное управление (оставляем как резервный вариант)
    new_stage = st.selectbox(
        "Этап (stage)",
        ["planning", "execution", "validation", "done"],
        index=["planning", "execution", "validation", "done"].index(working_data.get("stage", "planning"))
    )
    
    new_step = st.text_input("Текущий шаг (current_step)", value=working_data.get("current_step", ""))
    new_action = st.text_input("Ожидаемое действие (expected_action)", value=working_data.get("expected_action", ""))

    if st.button("💾 Сохранить статус FSM", type="primary"):
        agent.update_fsm(new_stage, new_step, new_action)
        st.success("Статус FSM успешно обновлен!")
        st.rerun()

    st.divider()

    # Просмотр сырых данных памяти (для отладки)
    with st.expander("📦 Просмотр всей памяти (JSON)"):
        st.json({
            "working": working_data,
            "long_term": long_term_data,
            "short_term_count": len(short_term_data)
        })

    st.divider()

    # Кнопка сброса
    if st.button("🔥 Сбросить всю память и FSM"):
        agent.reset_all_memory()
        st.success("Память и FSM сброшены к начальному состоянию!")
        st.rerun()

# --- ОСНОВНОЙ ЭКРАН (ЧАТ) ---
st.title("🔥 День 13. Состояние задачи (Task State Machine)")
st.markdown("Агент управляет задачей через конечный автомат: `Planning ➔ Execution ➔ Validation ➔ Done`.")
st.divider()

# Отображение истории сообщений
st_messages = agent.load_memory("short_term")
for msg in st_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Напишите ответ агенту...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Агент обрабатывает состояние задачи..."):
            try:
                res = agent.send_message(user_input)
                st.markdown(res["reply"])
                # ПРИНУДИТЕЛЬНЫЙ ПЕРЕЗАПУСК ДЛЯ ОБНОВЛЕНИЯ САЙДБАРА С FSM
                st.rerun()
            except Exception as e:
                st.error(str(e))
