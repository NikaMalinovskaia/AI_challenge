from __future__ import annotations
import json
import streamlit as st
from agent_day14 import InvariantTaskAgent

st.set_page_config(
    page_title="День 14: Инварианты и ограничения",
    page_icon="🛡️",
    layout="wide"
)

if "agent" not in st.session_state:
    st.session_state.agent = InvariantTaskAgent()

agent: InvariantTaskAgent = st.session_state.agent

# --- САЙДБАР ---
with st.sidebar:
    st.title("🛡️ День 14. Инварианты")
    st.markdown("Агент защищает систему от нарушения стека и бизнес-правил.")
    st.divider()

    # Загружаем текущие инварианты из файла
    inv_data = agent.load_memory("invariants")
    
    st.subheader("⚙️ Редактор инвариантов")
    
    inv_json_str = st.text_area(
        "JSON-конфигурация инвариантов", 
        value=json.dumps(inv_data, ensure_ascii=False, indent=2),
        height=280
    )

    if st.button("💾 Сохранить инварианты", type="primary"):
        try:
            parsed_inv = json.loads(inv_json_str)
            agent.update_invariants(parsed_inv)
            st.success("Инварианты успешно обновлены!")
            st.rerun()
        except json.JSONDecodeError as e:
            st.error(f"Ошибка в формате JSON: {e}")

    st.divider()
    
    # КНОПКА СБРОСА ЧАТА (Краткосрочной памяти)
    if st.button("🧹 Очистить историю чата"):
        agent.save_memory("short_term", [])
        st.success("История чата очищена!")
        st.rerun()

    # Кнопка полного сброса
    if st.button("🔥 Сбросить всё к дефолту"):
        agent.reset_all_memory()
        st.success("Память и инварианты сброшены!")
        st.rerun()

# --- ОСНОВНОЙ ЭКРАН (ЧАТ) ---
st.title("🛡️ День 14. Агент с инвариантами состояния")
st.markdown("Изменяйте инварианты слева в сайдбаре и проверяйте, как агент подстраивается под новые правила!")
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
        with st.spinner("Агент проверяет инварианты..."):
            try:
                res = agent.send_message(user_input)
                st.markdown(res["reply"])
            except Exception as e:
                st.error(str(e))
