import streamlit as st
from agent import LLMAgent # Убедись, что импорт совпадает с названием твоего файла

st.set_page_config(page_title="Day 6: AI Agent", page_icon="🤖")

st.title("🤖 AI Challenge - День 6: Первый агент")
st.write("Веб-интерфейс для агента. Память инкапсулирована внутри класса агента.")

# Боковая панель с настройками
with st.sidebar:
    st.header("Настройки агента")
    selected_model = st.selectbox("Модель", ["glm-4.7-flash", "glm-4"], index=0)
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
    
    st.divider()
    st.header("Управление сессией")
    
    if st.button("🔄 Очистить чат"):
        if "agent" in st.session_state:
            st.session_state.agent.reset_memory() # Вызываем новый метод агента
        st.rerun()
        
    if st.button("🏁 Завершить диалог и сохранить"):
        # Проверяем, есть ли сообщения кроме системного (len > 1)
        if "agent" in st.session_state and len(st.session_state.agent.messages) > 1:
            report = f"# Отчет: День 6 (Веб-агент Streamlit)\n\n"
            # Пропускаем системный промпт (индекс 0) при формировании отчета
            for msg in st.session_state.agent.messages[1:]:
                role = "Пользователь" if msg["role"] == "user" else "Агент"
                report += f"**{role}:** {msg['content']}\n\n"
            
            with open("agent_output.md", "w", encoding="utf-8") as f:
                f.write(report)
            st.success("Диалог завершен! Отчет сохранен в agent_output.md")
        else:
            st.warning("История диалога пуста.")

# Инициализируем агента, если его нет или изменились настройки
if "agent" not in st.session_state or \
   st.session_state.get("model_name") != selected_model or \
   st.session_state.get("temperature") != temperature:
    
    st.session_state.agent = LLMAgent(model_name=selected_model, temperature=temperature)
    st.session_state.model_name = selected_model
    st.session_state.temperature = temperature

# Отрисовываем историю чата, беря её НАПРЯМУЮ из агента (пропуская системный промпт)
for msg in st.session_state.agent.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Обработка ввода пользователя
if user_input := st.chat_input("Напишите сообщение агенту..."):
    # Сразу отображаем ввод пользователя
    with st.chat_message("user"):
        st.markdown(user_input)

    # Отправляем запрос агенту
    with st.chat_message("assistant"):
        with st.spinner("Агент думает..."):
            try:
                # Агент сам добавит сообщения в свою историю
                response_text = st.session_state.agent.chat(user_input)
                st.markdown(response_text)
            except Exception as e:
                st.error(f"Ошибка: {e}")                error_msg = f"Ошибка: {e}"
                st.error(error_msg)
