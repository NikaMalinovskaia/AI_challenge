import streamlit as st
from agent import CompressionAgent

st.set_page_config(page_title="День 9: Раздельное хранение Summary", page_icon="📦", layout="wide")

if "agent" not in st.session_state:
    st.session_state.agent = CompressionAgent()

agent = st.session_state.agent
chats_data = agent.get_all_chats()

if "active_chat_id" not in st.session_state or st.session_state.active_chat_id not in chats_data:
    if chats_data:
        st.session_state.active_chat_id = max(chats_data.keys(), key=int)
    else:
        st.session_state.active_chat_id = agent.create_new_chat()
        chats_data = agent.get_all_chats()

active_id = st.session_state.active_chat_id
chat_info = agent.load_chat_data(active_id)
messages = chat_info["messages"] # Только последние сообщения "как есть"
summary = chat_info.get("summary", "")

# --- САЙДБАР ---
with st.sidebar:
    if st.button("✏️ Новый диалог", use_container_width=True):
        new_id = agent.create_new_chat()
        st.session_state.active_chat_id = new_id
        agent.last_compression_stats = None
        st.rerun()

    st.divider()
    st.header("📦 Настройки компрессии")
    auto_threshold = st.slider("Сжимать каждые N сообщений", min_value=4, max_value=20, value=8, step=2)
    keep_n = st.slider("Оставлять последних сообщений 'как есть'", min_value=2, max_value=8, value=4, step=1)

    prepared_msgs = agent.get_prepared_request_messages(chat_info)
    raw_tokens = agent.count_messages_tokens(chat_info.get("full_history_backup", []))
    compressed_tokens = agent.count_messages_tokens(prepared_msgs)
    
    st.metric(label="Токенов в полной истории", value=raw_tokens)
    st.metric(label="Токенов в запросе (Summary + N)", value=compressed_tokens, delta=f"-{raw_tokens - compressed_tokens} ток.", delta_color="inverse")

    if st.button("⚡ Сжать историю сейчас", use_container_width=True):
        success = agent.compress_history(active_id, keep_last_n=keep_n)
        if success:
            st.success("История сжата!")
            st.rerun()
        else:
            st.warning("Мало сообщений для сжатия.")

    st.divider()
    st.markdown("### 💬 Ваши чаты")
    sorted_ids = sorted(chats_data.keys(), key=int, reverse=True)
    for cid in sorted_ids:
        title = chats_data[cid].get("title", "Диалог")
        is_active = (cid == active_id)
        label = f"💬 {title}" if not is_active else f"👉 [{title}]"
        
        c1, c2 = st.columns([0.8, 0.2])
        with c1:
            if st.button(label, key=f"sel_{cid}", use_container_width=True):
                st.session_state.active_chat_id = cid
                agent.last_compression_stats = None
                st.rerun()
        with c2:
            if st.button("🗑️", key=f"del_{cid}"):
                agent.delete_chat(cid)
                remaining = agent.get_all_chats()
                if remaining:
                    st.session_state.active_chat_id = max(remaining.keys(), key=int)
                else:
                    st.session_state.active_chat_id = agent.create_new_chat()
                agent.last_compression_stats = None
                st.rerun()

# --- ОСНОВНОЙ ЭКРАН ---
st.title("📦 День 9. Раздельное хранение Summary и подстановка в запрос")
st.markdown("Теперь `summary` хранится в файле чата **отдельно**, а в запрос подставляется динамически вместе с последними сообщениями.")

if agent.last_compression_stats:
    stats = agent.last_compression_stats
    with st.expander("📊 Отчет об экономии токенов", expanded=True):
        c1, c2, c3 = st.columns(3)
        c1.metric("До сжатия", stats["tokens_before"])
        c2.metric("После сжатия", stats["tokens_after"])
        c3.metric("Экономия", f"-{stats['saved_tokens']} ток.", delta_color="inverse")
        st.success(f"**Созданное Summary (хранится отдельно):** {stats['summary']}")

# Если есть отдельное summary, выведем его красивым блоком сверху
if summary:
    with st.expander("📌 Отдельно сохраненный контекст (Summary)", expanded=True):
        st.markdown(summary)

# Вывод последних сообщений "как есть"
for msg in messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

user_input = st.chat_input("Напишите сообщение...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.spinner("Агент обрабатывает запрос..."):
        try:
            result = agent.send_message(
                active_id, 
                user_input, 
                auto_compress_threshold=auto_threshold, 
                keep_last_n=keep_n
            )
            st.rerun()
        except Exception as e:
            st.error(str(e))
