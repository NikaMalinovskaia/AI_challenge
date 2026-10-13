import streamlit as st
import requests
import time
import concurrent.futures
from agent_rag import LocalRAGAgent

st.set_page_config(page_title="Day 30: Private AI Service", page_icon="🌐", layout="wide")

st.title("🌐 AI Challenge - День 30: Локальная LLM как приватный сервис")
st.write("Управление локальным AI-сервисом через HTTP API с мониторингом стабильности и нагрузки.")

if "rag_agent" not in st.session_state:
    st.session_state.rag_agent = LocalRAGAgent()

agent = st.session_state.rag_agent

# Сайдбар управления
with st.sidebar:
    st.header("⚙️ Конфигурация сервиса")
    server_url = st.text_input("API Endpoint", "http://localhost:11434/api/generate")
    selected_model = st.selectbox("Модель сервиса", ["qwen2.5"], index=0)
    temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.1)
    max_tokens = st.slider("Max Tokens (Rate Limit)", 100, 1000, 400, 50)
    
    st.header("📝 Шаблон промпта")
    prompt_template = st.selectbox(
        "Выберите роль/шаблон", 
        ["Стандартный", "Строгий код-ревьюер", "Преподаватель-наставник"]
    )
    
    agent.temperature = temperature
    agent.max_tokens = max_tokens
    
    st.divider()
    if st.button("🔄 Очистить чат"):
        agent.reset_memory()
        st.rerun()

# Вкладки: чат с сервисом + панель мониторинга и нагрузки
tab_chat, tab_service = st.tabs(["💬 Чат с AI-сервисом", "📊 Мониторинг и тест API нагрузки"])

with tab_chat:
    st.write("Общение с локальным приватным сервисом через RAG-пайплайн.")
    
    for msg in agent.history:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant"):
                st.markdown(msg["content"])
                
    if user_input := st.chat_input("Введите запрос к сервису или вставьте код на C#..."):
        with st.chat_message("user"):
            st.markdown(user_input)
            
        with st.chat_message("assistant"):
            with st.spinner("Запрос к локальному HTTP API..."):
                try:
                    ans, sources, dur = agent.chat_single(user_input, prompt_template)
                    st.markdown(ans)
                    with st.expander("📡 HTTP API метрики"):
                        st.write(f"⏱ **Время ответа:** {dur:.2f} сек.")
                        st.write(f"🔗 **Эндпоинт:** {server_url}")
                except Exception as e:
                    st.error(f"Ошибка сервиса: {e}")

with tab_service:
    st.header("⚡ Стресс-тест и проверка стабильности API")
    st.write("Проверка отклика приватного сервиса при одновременной отправке нескольких запросов (симуляция высокой нагрузки).")
    
    test_prompt = st.text_input("Промпт для стресс-теста", "Объясни в одном предложении суть ООП.")
    num_threads = st.slider("Количество параллельных потоков", 1, 5, 3)
    
    if st.button("🚀 Запустить нагрузочный тест"):
        st.write(f"Отправка {num_threads} параллельных запросов на `{server_url}`...")
        
        def single_request(p):
            start = time.time()
            try:
                # Обертка запроса в позитивный языковой контекст для стресс-теста
                formatted_prompt = (
                    "Роль: Ассистент по программированию на C#. Язык ответа: строго русский.\n\n"
                    f"Запрос: {p}"
                )
                payload = {
                    "model": selected_model,
                    "prompt": formatted_prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature, 
                        "num_predict": max_tokens
                    }
                }
                res = requests.post(server_url, json=payload, timeout=90)
                dur = time.time() - start
                if res.status_code == 200:
                    return {"status": "success", "duration": dur, "text": res.json().get("response", "").strip()}
                else:
                    return {"status": f"HTTP Error {res.status_code}", "duration": dur}
            except Exception as e:
                return {"status": f"Connection Error: {e}", "duration": time.time() - start}

        prompts_list = [test_prompt for _ in range(num_threads)]
        
        results_container = st.container()
        start_time_total = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(single_request, p) for p in prompts_list]
            
            with results_container:
                for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
                    res = future.result()
                    if res["status"] == "success":
                        st.success(f"Запрос {i}: Успешно за {res['duration']:.2f} сек.")
                        st.code(res["text"][:150] + "...")
                    else:
                        st.error(f"Запрос {i}: Ошибка — {res['status']}")
                        
        total_duration = time.time() - start_time_total
        st.info(f"🏁 Общее время выполнения стресс-теста: {total_duration:.2f} сек.")
