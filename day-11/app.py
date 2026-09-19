import streamlit as st
from agent_day11 import TieredMemoryAgent

st.set_page_config(page_title="День 11: Модель памяти агента", page_icon="🧠", layout="wide")

st.title("🔥 День 11. Явная модель памяти агента")
st.info("Информация разделена на 3 слоя: Краткосрочная (диалог), Рабочая (задача) и Долговременная (профиль). Вы можете явно наполнять их через сайдбар.")

# --- САЙДБАР: НАСТРОЙКИ И УПРАВЛЕНИЕ ПАМЯТЬЮ ---
with st.sidebar:
    st.header("⚙️ Настройки агента")
    selected_model = st.selectbox("Модель", ["glm-4.7-flash", "glm-5.3-flash", "deepseek-v4-flash-0731"], index=0)
    temperature = st.slider("Temperature", 0.0, 1.0, 0.3, 0.1)
    
    st.divider()
    st.header("🧠 Слои памяти")
    
    # Инициализируем агента, если его нет или изменились настройки
    if "agent" not in st.session_state or \
       st.session_state.get("model_name") != selected_model or \
       st.session_state.get("temperature") != temperature:
        st.session_state.agent = TieredMemoryAgent(model_name=selected_model, temperature=temperature)
        st.session_state.model_name = selected_model
        st.session_state.temperature = temperature

    agent = st.session_state.agent

    # 1. Долговременная память
    st.subheader("1. Долговременная (Long-Term)")
    lt_data = agent.load_memory("long_term")
    st.json(lt_data)
    
    with st.form("lt_form", clear_on_submit=True):
        lt_key = st.text_input("Ключ (например: pref_lang)", key="lt_key_input")
        lt_val = st.text_input("Значение (например: Python)", key="lt_val_input")
        if st.form_submit_button("Сохранить в Long-Term"):
            if lt_key and lt_val:
                agent.explicit_save("long_term", lt_key, lt_val)
                st.success("Сохранено в долговременную память!")
                st.rerun()

    st.divider()

    # 2. Рабочая память
    st.subheader("2. Рабочая память (Working)")
    wk_data = agent.load_memory("working")
    st.json(wk_data)
    
    with st.form("wk_form", clear_on_submit=True):
        wk_key = st.text_input("Ключ задачи (например: budget)", key="wk_key_input")
        wk_val = st.text_input("Значение задачи (например: $5000)", key="wk_val_input")
        if st.form_submit_button("Сохранить в Working"):
            if wk_key and wk_val:
                agent.explicit_save("working", wk_key, wk_val)
                st.success("Сохранено в рабочую память!")
                st.rerun()

    st.divider()

    # 3. Краткосрочная память
    st.subheader("3. Краткосрочная (Short-Term)")
    st_data = agent.load_memory("short_term")
    st.text(f"Всего реплик в истории: {len(st_data)}")
    
    if st.button("🧹 Очистить краткосрочную память"):
        agent.reset_short_term()
        st.success("Диалог очищен!")
        st.rerun()

    st.divider()
    
    # Кнопка полного сброса
    if st.button("🔥 Сбросить всю память и чат", type="primary"):
        agent.reset_all_memory()
        st.success("Вся память и чат полностью сброшены!")
        st.rerun()

# --- ОСНОВНОЙ ЭКРАН (ЧАТ) ---
st_messages = agent.load_memory("short_term")
for msg in st_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Задайте вопрос или дайте вводные по задаче...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Агент думает с учетом всех слоев памяти..."):
            try:
                res = agent.send_message(user_input)
                st.markdown(res["reply"])
            except Exception as e:
                st.error(str(e))
