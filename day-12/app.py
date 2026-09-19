import streamlit as st
from agent_day12 import PersonalizedAgent

st.set_page_config(page_title="День 12: Персонализация ассистента", page_icon="👤", layout="wide")

st.title("🔥 День 12. Персонализация ассистента")
st.info("Агент автоматически подстраивает тон, стиль, формат ответов и ограничения под ваш профиль (Long-Term), заданный в настройках.")

# --- САЙДБАР ---
with st.sidebar:
    st.header("⚙️ Настройки")
    selected_model = st.selectbox("Модель", ["glm-4.7-flash", "glm-5.3-flash", "deepseek-v4-flash-0731"], index=0)
    temperature = st.slider("Temperature", 0.0, 1.0, 0.3, 0.1)
    
    st.divider()
    st.header("👤 Профиль (Long-Term)")
    
    if "agent" not in st.session_state or \
       st.session_state.get("model_name") != selected_model or \
       st.session_state.get("temperature") != temperature:
        st.session_state.agent = PersonalizedAgent(model_name=selected_model, temperature=temperature)
        st.session_state.model_name = selected_model
        st.session_state.temperature = temperature

    agent = st.session_state.agent

    lt_data = agent.load_memory("long_term")
    st.json(lt_data)
    
    with st.form("lt_form", clear_on_submit=True):
        lt_key = st.text_input("Параметр профиля (например: tone)", key="lt_key_input")
        lt_val = st.text_input("Значение (например: ироничный)", key="lt_val_input")
        if st.form_submit_button("Обновить профиль"):
            if lt_key and lt_val:
                agent.explicit_save("long_term", lt_key, lt_val)
                st.success("Профиль обновлен!")
                st.rerun()

    st.divider()
    st.subheader("🛠️ Рабочая память (Заданиe)")
    wk_data = agent.load_memory("working")
    st.json(wk_data)
    
    with st.form("wk_form", clear_on_submit=True):
        wk_key = st.text_input("Ключ задачи", key="wk_key_input")
        wk_val = st.text_input("Значение задачи", key="wk_val_input")
        if st.form_submit_button("Сохранить в Working"):
            if wk_key and wk_val:
                agent.explicit_save("working", wk_key, wk_val)
                st.success("Сохранено в задачу!")
                st.rerun()

    st.divider()
    if st.button("🔥 Сбросить всю память и чат", type="primary"):
        agent.reset_all_memory()
        st.success("Сброшено до дефолтного профиля Senior!")
        st.rerun()

# --- ОСНОВНОЙ ЭКРАН (ЧАТ) ---
st_messages = agent.load_memory("short_term")
for msg in st_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Задайте вопрос для проверки персонализации...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Генерация персонализированного ответа..."):
            try:
                res = agent.send_message(user_input)
                st.markdown(res["reply"])
            except Exception as e:
                st.error(str(e))
