import streamlit as st
from agent import TokenAgent

st.set_page_config(page_title="День 8: Трекер токенов и чаты", page_icon="📊", layout="wide")

if "agent" not in st.session_state:
    st.session_state.agent = TokenAgent()

agent = st.session_state.agent
chats_data = agent.get_all_chats()

if "active_chat_id" not in st.session_state or st.session_state.active_chat_id not in chats_data:
    if chats_data:
        st.session_state.active_chat_id = max(chats_data.keys(), key=int)
    else:
        st.session_state.active_chat_id = agent.create_new_chat()
        chats_data = agent.get_all_chats()

active_id = st.session_state.active_chat_id
messages = agent.load_chat(active_id)

# --- САЙДБАР: Переключение чатов и лимиты ---
with st.sidebar:
    if st.button("✏️ Новый диалог", use_container_width=True):
        new_id = agent.create_new_chat()
        st.session_state.active_chat_id = new_id
        agent.last_attempt = None
        st.rerun()

    st.divider()
    st.header("⚙️ Лимиты и аналитика")
    model_limit = st.slider("Лимит модели (токенов)", min_value=200, max_value=15000, value=1200, step=100)
    
    history_tokens = agent.count_messages_tokens(messages)
    
    # Если была попытка отправки запроса, показываем честную сумму с учетом запроса в сайдбаре
    if agent.last_attempt:
        display_total = agent.last_attempt["total_input_tokens"]
        st.metric(label="Токенов на входе (История + Запрос)", value=display_total, delta=f"Лимит: {model_limit}")
    else:
        display_total = history_tokens
        st.metric(label="Токенов в текущей истории", value=display_total)
    
    usage_ratio = min(display_total / model_limit, 1.0)
    st.progress(usage_ratio, text=f"Заполнение: {int(usage_ratio * 100)}% ({display_total}/{model_limit})")

    if display_total >= model_limit:
        st.error(f"🚨 Переполнение в сайдбаре!\nСуммарно: {display_total} токенов при лимите {model_limit}.")

    st.divider()
    st.markdown("### 💬 История ваших чатов")
    
    sorted_ids = sorted(chats_data.keys(), key=int, reverse=True)
    for cid in sorted_ids:
        title = chats_data[cid].get("title", "Диалог")
        is_active = (cid == active_id)
        label = f"💬 {title}" if not is_active else f"👉 [{title}]"
        
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            if st.button(label, key=f"sel_{cid}", use_container_width=True):
                st.session_state.active_chat_id = cid
                agent.last_attempt = None
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{cid}"):
                agent.delete_chat(cid)
                remaining = agent.get_all_chats()
                if remaining:
                    st.session_state.active_chat_id = max(remaining.keys(), key=int)
                else:
                    st.session_state.active_chat_id = agent.create_new_chat()
                agent.last_attempt = None
                st.rerun()

# --- ОСНОВНОЙ ЭКРАН ---
st.title("🔥 День 8. Работа с токенами и историей")
st.markdown("Теперь сайдбар мгновенно подсвечивает переполнение при отправке массивных запросов.")

# Вывод истории текущего чата
for msg in messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Напишите сообщение...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.spinner("Агент обрабатывает запрос и считает токены..."):
        try:
            result = agent.send_message(active_id, user_input, model_limit=model_limit)
            
            with st.expander("📊 Детализация токенов этого запроса", expanded=True):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Текущий запрос", result["request_tokens"])
                c2.metric("История до запроса", result["history_tokens"])
                c3.metric("Ответ модели", result["response_tokens"])
                c4.metric("Всего накоплено", result["cumulative_tokens"])
            
            st.rerun()
        except Exception as e:
            st.error(str(e))
            st.rerun()
