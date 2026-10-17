import streamlit as st
import json
import os
from agent import LLMAgent

st.set_page_config(page_title="Day 7: Persistent AI Agent", page_icon="🤖")

st.title("🤖 AI Challenge - День 7: Сохранение контекста")
st.write("Веб-интерфейс с персистентной памятью, сохраняющейся в JSON-файл.")

# Инициализируем агента в session_state (если еще не создан)
if "agent" not in st.session_state:
    st.session_state.agent = LLMAgent()

# Боковая панель
with st.sidebar:
    st.header("Настройки и Статус")
    
    # Индикатор состояния памяти
    if st.session_state.agent.loaded_from_disk:
        st.success("📂 Контекст успешно восстановлен из `chat_history.json`!")
    else:
        st.info("🆕 Начата новая сессия (файл пуст или создан заново).")
        
    st.divider()
    st.header("Управление сессией")
    
    if st.button("🔄 Очистить чат и память"):
        st.session_state.agent.reset_memory()
        st.rerun()
        
    if st.button("🏁 Завершить диалог и сохранить отчет"):
        if len(st.session_state.agent.messages) > 1:
            report = f"# Отчет: День 7 (Персистентный агент)\n\n"
            for msg in st.session_state.agent.messages[1:]:
                role = "Пользователь" if msg["role"] == "user" else "Агент"
                report += f"**{role}:** {msg['content']}\n\n"
            
            with open("agent_output.md", "w", encoding="utf-8") as f:
                f.write(report)
            st.success("Отчет сохранен в agent_output.md")
        else:
            st.warning("История пуста.")

    st.divider()
    st.subheader("🔍 Отладка: JSON на диске")
    # Красиво показываем содержимое файла chat_history.json в сайдбаре
    if os.path.exists("chat_history.json"):
        with open("chat_history.json", "r", encoding="utf-8") as f:
            raw_json = f.read()
        st.code(raw_json, language="json")
    else:
        st.text("Файл истории пока не создан.")

# Отрисовываем историю чата (пропуская системный промпт)
for msg in st.session_state.agent.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Обработка ввода пользователя
if user_input := st.chat_input("Напишите сообщение агенту..."):
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Агент думает..."):
            try:
                response_text = st.session_state.agent.chat(user_input)
                st.markdown(response_text)
                # Перезагружаем страницу, чтобы обновить блок с JSON в сайдбаре
                st.rerun()
            except Exception as e:
                st.error(f"Ошибка: {e}")
