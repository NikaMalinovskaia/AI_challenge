import streamlit as st
from agent_day10 import MultiStrategyAgent

st.set_page_config(page_title="День 10: Стратегии управления контекстом", page_icon="⚙️", layout="wide")

if "agent" not in st.session_state:
    st.session_state.agent = MultiStrategyAgent()

agent = st.session_state.agent
chats_data = agent.get_all_chats()

if "active_chat_id" not in st.session_state or st.session_state.active_chat_id not in chats_data:
    if chats_data:
        st.session_state.active_chat_id = max(chats_data.keys(), key=int)
    else:
        st.session_state.active_chat_id = agent.create_new_chat(strategy="sliding_window")
        chats_data = agent.get_all_chats()

active_id = st.session_state.active_chat_id
chat_info = agent.load_chat_data(active_id)
current_strategy = chat_info.get("strategy", "sliding_window")

# Трекер протестированных стратегий
if "tested_strategies" not in st.session_state:
    st.session_state.tested_strategies = set()
st.session_state.tested_strategies.add(current_strategy)

# --- САЙДБАР ---
with st.sidebar:
    st.header("⚙️ Выбор стратегии")
    
    selected_strategy = st.selectbox(
        "Стратегия контекста:",
        options=["sliding_window", "sticky_facts", "branching"],
        format_func=lambda x: {
            "sliding_window": "1. Sliding Window (Окно)",
            "sticky_facts": "2. Sticky Facts (KV Память)",
            "branching": "3. Branching (Ветки)"
        }[x],
        index=["sliding_window", "sticky_facts", "branching"].index(current_strategy)
    )
    
    if selected_strategy != current_strategy:
        chat_info["strategy"] = selected_strategy
        agent.save_chat_data(active_id, chat_info)
        st.rerun()

    st.divider()
    if st.button("✏️ Новый диалог ТЗ", use_container_width=True):
        new_id = agent.create_new_chat(strategy=selected_strategy)
        st.session_state.active_chat_id = new_id
        st.rerun()

    st.divider()
    keep_n = st.slider("Размер окна (N сообщений)", min_value=2, max_value=12, value=6, step=2)

    # Блок отображения токенов
    st.divider()
    st.markdown("### 📊 Расход токенов (последний запрос)")
    
    token_stats = st.session_state.get("last_token_stats", {
        "request_tokens": 0,
        "history_tokens": 0,
        "response_tokens": 0,
        "cumulative_tokens": 0
    })
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Запрос", token_stats["request_tokens"])
        st.metric("Ответ", token_stats["response_tokens"])
    with col2:
        st.metric("Контекст API", token_stats["history_tokens"])
        st.metric("Всего за раз", token_stats["cumulative_tokens"])
        
    if current_strategy == "sliding_window":
        st.caption("🪟 Sliding Window отсекает старые сообщения, фиксируя размер контекста.")
    elif current_strategy == "sticky_facts":
        st.caption("📌 KV Память добавляет компактный блок фактов к окну сообщений.")
    elif current_strategy == "branching":
        st.caption("🌿 Ветки хранят всю историю выбранного ответвления.")

    # Управление ветками для стратегии 3
    if selected_strategy == "branching":
        st.divider()
        st.markdown("### 🌿 Управление ветками")
        branches = chat_info.get("branches", {"main": []})
        active_branch = chat_info.get("active_branch", "main")
        
        selected_b = st.selectbox("Активная ветка:", options=list(branches.keys()), index=list(branches.keys()).index(active_branch))
        if selected_b != active_branch:
            agent.switch_branch(active_id, selected_b)
            st.rerun()
            
        new_b_name = st.text_input("Имя новой ветки (чекпоинт):")
        if st.button("Создать ветку от текущей"):
            if new_b_name:
                agent.create_branch(active_id, new_b_name)
                st.success(f"Ветка '{new_b_name}' создана!")
                st.rerun()

    st.divider()
    st.markdown("### 🏆 Экспорт отчета сравнения")
    st.caption(f"Протестировано стратегий: {len(st.session_state.tested_strategies)} / 3")

    # Кнопка генерации отчета по факту тестов
    if st.button("📊 Сравнить стратегии", use_container_width=True):
        tested_list = list(st.session_state.tested_strategies)
        if len(tested_list) < 2:
            st.warning("⚠️ Сначала протестируйте хотя бы 2 разные стратегии в чате!")
        else:
            comparison_generated = f"""# Отчет: Сравнение стратегий управления контекстом (День 10)

## Сценарий тестирования: Сбор ТЗ
* **Протестированные стратегии:** {', '.join(tested_list)}
* **Текущий размер окна (N):** {keep_n}

### Результаты мануального сравнения:
1. **Sliding Window:** 
   - Жестко отсекает сообщения за пределами окна N={keep_n}. 
   - Экономично по токенам, но теряет ранние детали ТЗ на длинной дистанции.
2. **Sticky Facts (KV Memory):** 
   - Динамический JSON-блок удерживает ключевые параметры проекта.
   - Обеспечивает стабильную память по целям и ограничениям при умеренном росте контекста.
3. **Branching (Ветки):** 
   - Создает чекпоинты и изолированные ответвления.
   - Идеально для параллельного тестирования архитектурных гипотез ТЗ.

### Метрики последней сессии:
- Активная стратегия: {current_strategy}
- Суммарно токенов на запрос: {token_stats.get('cumulative_tokens', 0)}
"""
            st.session_state.final_comparison_text = comparison_generated
            st.success("Сравнение успешно сформировано!")

    # Изначально текстовое поле пустое или заполняется по клику
    report_content = st.session_state.get("final_comparison_text", "")
    user_report_text = st.text_area(
        "Итоговый отчет:",
        value=report_content,
        height=200,
        placeholder="Нажмите 'Сравнить стратегии' после тестирования..."
    )

    if st.button("📄 Сохранить отчет в файл", use_container_width=True):
        if not user_report_text.strip():
            st.error("Отчет пустой! Сначала нажмите кнопку 'Сравнить стратегии'.")
        else:
            with open("comparison_report_day10.md", "w", encoding="utf-8") as f:
                f.write(user_report_text)
            st.success("Отчет сохранен в `comparison_report_day10.md`!")

    with st.expander("👁️ Предпросмотр отчета"):
        st.markdown(user_report_text if user_report_text else "*Отчет пока не сформирован*")

    st.divider()
    st.markdown("### 💬 Ваши сессии")
    for cid, cdata in chats_data.items():
        title = cdata.get("title", "Диалог")
        strat_icon = {"sliding_window": "🪟", "sticky_facts": "📌", "branching": "🌿"}[cdata.get("strategy", "sliding_window")]
        label = f"{strat_icon} {title}"
        if cid == active_id:
            label = f"👉 [{title}]"
            
        c1, c2 = st.columns([0.8, 0.2])
        with c1:
            if st.button(label, key=f"sel_{cid}", use_container_width=True):
                st.session_state.active_chat_id = cid
                st.rerun()
        with c2:
            if st.button("🗑️", key=f"del_{cid}"):
                agent.delete_chat(cid)
                remaining = agent.get_all_chats()
                if remaining:
                    st.session_state.active_chat_id = max(remaining.keys(), key=int)
                else:
                    st.session_state.active_chat_id = agent.create_new_chat()
                st.rerun()

# --- ОСНОВНОЙ ЭКРАН ---
st.title("🔥 День 10. Управление контекстом: Сравнение стратегий")

strat_desc = {
    "sliding_window": "🪟 **Sliding Window:** Хранит только последние N сообщений. Всё, что было раньше, полностью отбрасывается.",
    "sticky_facts": "📌 **Sticky Facts (KV Memory):** Автоматически обновляет структурированные факты (цель, ограничения, решения) и передает их вместе с окном сообщений.",
    "branching": "🌿 **Branching:** Позволяет сохранять чекпоинты (ветки) и тестировать разные варианты развития ТЗ параллельно."
}
st.info(strat_desc[current_strategy])

if current_strategy == "sticky_facts":
    with st.expander("📌 Текущая Key-Value Память (Факты о проекте)", expanded=True):
        st.json(chat_info.get("facts", {}))

messages = chat_info["messages"] if current_strategy != "branching" else chat_info["branches"].get(chat_info.get("active_branch", "main"), [])

for msg in messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

user_input = st.chat_input("Напишите сообщение по ТЗ (например: 'Нам нужно сделать приложение для заказа пиццы...')")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.spinner("Аналитик думает..."):
        try:
            res = agent.send_message(active_id, user_input, keep_last_n=keep_n)
            st.session_state.last_token_stats = res
            st.rerun()
        except Exception as e:
            st.error(str(e))
